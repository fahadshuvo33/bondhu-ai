# app/core/dependencies.py
from typing import Optional, Generator, Annotated
from datetime import datetime
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import redis
from functools import lru_cache

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import verify_token
from app.models.user import User, UserType
from app.models.auth import UserSession

# Security scheme
security = HTTPBearer()


# Redis client
@lru_cache()
def get_redis_client():
    """Get Redis client instance"""
    settings = get_settings()
    return redis.from_url(settings.redis_url, decode_responses=True)


# Get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    if user.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account suspended: {user.suspension_reason}",
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user with verified email or phone
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email or phone number",
        )
    return current_user


# Role-based dependencies
async def get_current_student(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> User:
    """Ensure current user is a student"""
    if current_user.user_type != UserType.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Student access required"
        )
    return current_user


async def get_current_teacher(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> User:
    """Ensure current user is a teacher"""
    if current_user.user_type != UserType.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Teacher access required"
        )
    return current_user


async def get_current_parent(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> User:
    """Ensure current user is a parent"""
    if current_user.user_type != UserType.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Parent access required"
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> User:
    """Ensure current user is an admin"""
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


# Optional user (for endpoints that work with or without auth)
async def get_optional_user(
    authorization: Optional[str] = Header(None), db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get user if token is provided, otherwise return None
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")

        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.is_active:
                return user
    except:
        pass

    return None


# Session validation
async def validate_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserSession:
    """
    Validate user session from token and request info
    """
    # Get session token from header or extract from JWT
    session_token = request.headers.get("X-Session-Token")

    if not session_token:
        # For now, we'll create a session if none exists
        return None

    session = (
        db.query(UserSession)
        .filter(
            UserSession.session_token == session_token,
            UserSession.user_id == current_user.id,
            UserSession.is_active == True,
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
        )

    if session.is_expired():
        session.is_active = False
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired"
        )

    # Update last activity
    session.last_activity_at = datetime.utcnow()
    db.commit()

    return session


# Rate limiting dependency
class RateLimiter:
    def __init__(self, times: int = 10, seconds: int = 60):
        self.times = times
        self.seconds = seconds

    def __call__(
        self, request: Request, current_user: User = Depends(get_current_user)
    ):
        redis_client = get_redis_client()
        key = f"rate_limit:{current_user.id}:{request.url.path}"

        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.seconds)
        result = pipe.execute()

        times = result[0]
        if times > self.times:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {self.seconds} seconds",
            )

        return True


# Common rate limiters
rate_limit_5_per_minute = RateLimiter(times=5, seconds=60)
rate_limit_10_per_minute = RateLimiter(times=10, seconds=60)
rate_limit_100_per_hour = RateLimiter(times=100, seconds=3600)


# Pagination dependencies
class PaginationParams:
    def __init__(self, page: int = 1, page_size: int = settings.DEFAULT_PAGE_SIZE):
        self.page = max(1, page)
        self.page_size = min(page_size, settings.MAX_PAGE_SIZE)
        self.skip = (self.page - 1) * self.page_size
        self.limit = self.page_size


# API Key validation (for external integrations)
async def validate_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"), db: Session = Depends(get_db)
):
    """Validate API key for external integrations"""
    # Implementation depends on your API key strategy
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Missing API key"
        )
    # Validate against database or settings
    return True


# Type aliases for cleaner code
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentStudent = Annotated[User, Depends(get_current_student)]
CurrentTeacher = Annotated[User, Depends(get_current_teacher)]
CurrentParent = Annotated[User, Depends(get_current_parent)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
DBSession = Annotated[Session, Depends(get_db)]
Pagination = Annotated[PaginationParams, Depends()]
