from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from app.models.base import BaseModel
from enum import Enum


class UserType(str, Enum):
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(BaseModel):
    """Core user model for authentication only"""

    __tablename__ = "users"

    # User type
    user_type = Column(
        SQLEnum(UserType), nullable=False, index=True, default=UserType.STUDENT
    )

    # Authentication identifiers (at least one required)
    email = Column(String, unique=True, nullable=True, index=True)
    phone_number = Column(String, unique=True, nullable=True, index=True)
    username = Column(String, unique=True, nullable=True, index=True)

    # Authentication
    hashed_password = Column(String, nullable=True)  # Optional for OAuth users

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)

    # Account flags
    is_suspended = Column(Boolean, default=False)
    suspension_reason = Column(String, nullable=True)
    suspended_at = Column(DateTime(timezone=True), nullable=True)

    # Last login tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Password reset
    password_reset_token = Column(String, nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)

    # Two-factor auth (future)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String, nullable=True)
