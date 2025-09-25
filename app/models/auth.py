# app/models/auth.py
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models._base import BaseModel
import secrets
from datetime import datetime, timedelta


class UserAuthMethod(BaseModel):
    """Track multiple auth methods for a user"""
    
    __tablename__ = "user_auth_methods"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    auth_type = Column(String, nullable=False)  # email, phone, google, facebook
    auth_identifier = Column(String, nullable=False)  # email address, phone, oauth_id
    is_verified = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=False)
    
    # OAuth specific
    oauth_provider = Column(String, nullable=True)  # google, facebook
    oauth_access_token = Column(Text, nullable=True)
    oauth_refresh_token = Column(Text, nullable=True)
    oauth_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="auth_methods")


class UserSession(BaseModel):
    """Track active user sessions"""
    
    __tablename__ = "user_sessions"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    session_token = Column(String, unique=True, index=True, nullable=False)
    
    # Session info
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String, nullable=True)  # mobile, desktop, tablet
    device_id = Column(String, nullable=True)  # for mobile apps
    
    # Location (optional)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    
    # Session management
    is_active = Column(Boolean, default=True)
    last_activity_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Security
    is_suspicious = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoke_reason = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", backref="sessions")
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at


class OTPVerification(BaseModel):
    """Handle OTP for phone/email verification"""
    
    __tablename__ = "otp_verifications"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    verification_type = Column(String, nullable=False)  # email, phone, 2fa
    destination = Column(String, nullable=False)  # email address or phone number
    otp_code = Column(String, nullable=False)
    
    # Tracking
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Status
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Rate limiting
    last_sent_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    send_count = Column(Integer, default=1)
    
    # Relationships
    user = relationship("User", backref="otp_verifications")
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def can_resend(self):
        # Can resend after 60 seconds
        return (datetime.utcnow() - self.last_sent_at).seconds > 60


class RefreshToken(BaseModel):
    """JWT Refresh token tracking"""
    
    __tablename__ = "refresh_tokens"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    
    # Token info
    device_id = Column(String, nullable=True)
    family = Column(String, nullable=False)  # Token family for rotation
    
    # Status
    is_active = Column(Boolean, default=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    replaced_by = Column(String, nullable=True)  # New token that replaced this
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Security
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", backref="refresh_tokens")


class LoginAttempt(BaseModel):
    """Track login attempts for security"""
    
    __tablename__ = "login_attempts"
    
    identifier = Column(String, index=True, nullable=False)  # email/phone/username
    attempt_type = Column(String, nullable=False)  # login, otp, password_reset
    
    # Result
    is_successful = Column(Boolean, default=False)
    failure_reason = Column(String, nullable=True)  # invalid_password, account_locked
    
    # Request info
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    country = Column(String, nullable=True)
    
    # User (if found)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user = relationship("User", backref="login_attempts")


class PasswordHistory(BaseModel):
    """Track password changes for security"""
    
    __tablename__ = "password_history"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    password_hash = Column(String, nullable=False)
    
    # Change info
    changed_by = Column(String, nullable=False)  # user, admin, system
    change_reason = Column(String, nullable=True)  # reset, expired, compromise
    
    # Request info
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", backref="password_history")