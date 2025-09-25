# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from passlib.hash import bcrypt
import secrets
import string
import re
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from sqlalchemy.sql.functions import now

from app.core.config import get_settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password against security requirements
    Returns: (is_valid, error_message)
    """
    settings = get_settings()
    if len(password) < getattr(settings, "PASSWORD_MIN_LENGTH", 8):
        return (
            False,
            f"Password must be at least {getattr(settings, 'PASSWORD_MIN_LENGTH', 8)} characters long",
        )

    if getattr(settings, "PASSWORD_REQUIRE_UPPERCASE", False) and not re.search(
        r"[A-Z]", password
    ):
        return False, "Password must contain at least one uppercase letter"

    if getattr(settings, "PASSWORD_REQUIRE_NUMBERS", False) and not re.search(
        r"\d", password
    ):
        return False, "Password must contain at least one number"

    if getattr(settings, "PASSWORD_REQUIRE_SPECIAL", False) and not re.search(
        r"[!@#$%^&*(),.?\":{}|<>]", password
    ):
        return False, "Password must contain at least one special character"

    return True, ""


# Token utilities
def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.now(timezone.utc),
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    device_id: Optional[str] = None,
) -> str:
    """Create JWT refresh token"""
    if expires_delta:
        expire = datetime.now(timezone) + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(32),  # JWT ID for token rotation
    }

    if device_id:
        to_encode["device_id"] = device_id

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token
    Returns payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # Verify token type
        if payload.get("type") != token_type:
            return None

        return payload
    except JWTError:
        return None


# OTP utilities
def generate_otp(length: int = 6) -> str:
    """Generate numeric OTP"""
    return "".join(secrets.choice(string.digits) for _ in range(length))


def generate_secure_token(length: int = 32) -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(length)


# Session token
def generate_session_token() -> str:
    """Generate unique session token"""
    return secrets.token_urlsafe(64)


# API key generation
def generate_api_key() -> str:
    """Generate API key for external integrations"""
    prefix = "bai"  # Bondhu AI
    key = secrets.token_urlsafe(32)
    return f"{prefix}_{key}"


# Email/Phone validation
def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Validate Bangladesh phone number"""
    # Remove any spaces or dashes
    phone = re.sub(r"[\s-]", "", phone)

    # Bangladesh phone patterns
    # +8801XXXXXXXXX or 01XXXXXXXXX
    pattern = r"^(?:\+?880)?1[3-9]\d{8}$"
    return re.match(pattern, phone) is not None


def format_phone(phone: str) -> str:
    """Format phone number to standard format"""
    # Remove all non-digits
    phone = re.sub(r"\D", "", phone)

    # Remove country code if present
    if phone.startswith("880"):
        phone = phone[3:]

    # Add country code
    return f"+880{phone}"


# Security headers
def get_security_headers() -> Dict[str, str]:
    """Get security headers for responses"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }


# IP validation and extraction
def get_client_ip(request) -> str:
    """Extract client IP from request"""
    # Check for proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host


# Two-factor authentication (if enabled)
def generate_2fa_secret() -> str:
    """Generate 2FA secret for TOTP"""
    import pyotp

    return pyotp.random_base32()


def verify_2fa_token(secret: str, token: str) -> bool:
    """Verify 2FA TOTP token"""
    import pyotp

    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)
