from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from enum import Enum


class AuthProvider(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    APPLE = "apple"


class UserAuthMethod(Base):
    """Track all authentication methods for a user"""

    __tablename__ = "user_auth_methods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    provider = Column(SQLEnum(AuthProvider))
    identifier = Column(String)  # email, phone, or social ID

    # For social logins
    provider_user_id = Column(String, nullable=True)
    provider_data = Column(String, nullable=True)  # JSON string

    is_primary = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Unique constraint: one identifier per provider
    __table_args__ = (
        UniqueConstraint("provider", "identifier", name="uq_provider_identifier"),
    )

    # Relationships
    user = relationship("User", back_populates="auth_methods")


class UserSession(Base):
    """Track active sessions for security"""

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    refresh_token_jti = Column(String, unique=True, index=True)  # JWT ID

    device_info = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())

    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="sessions")


class OTPVerification(Base):
    """Store OTP codes for verification"""

    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, index=True)

    identifier = Column(String, index=True)  # email or phone
    identifier_type = Column(String)  # 'email' or 'phone'

    otp_code = Column(String)
    purpose = Column(String)  # 'login', 'register', 'reset_password', 'add_method'

    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    verified_at = Column(DateTime(timezone=True), nullable=True)

    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # For adding methods to existing user
