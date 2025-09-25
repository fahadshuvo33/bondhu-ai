from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models._base import BaseModel
from enum import Enum


class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"  # You - can do everything
    ADMIN = "admin"  # Full admin but can't modify super_admin
    MODERATOR = "moderator"  # Can moderate content, users
    SUPPORT = "support"  # Can help users, view data
    CONTENT_MANAGER = "content_manager"  # Can manage educational content


class Admin(BaseModel):
    """Admin-specific information"""

    __tablename__ = "admins"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True
    )

    # Admin info
    employee_id = Column(String, unique=True, nullable=False)

    # Role and permissions
    admin_role = Column(String, nullable=False)  # Using AdminRole enum
    permissions = Column(Text, nullable=True)  # JSON array of specific permissions

    # Department
    department = Column(String, nullable=True)  # tech, support, content, finance

    # Activity tracking
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    total_actions = Column(Integer, default=0)

    # Access restrictions
    ip_whitelist = Column(Text, nullable=True)  # JSON array of allowed IPs
    require_2fa = Column(Boolean, default=True)

    # Who created this admin (for audit)
    created_by_admin_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="admin", uselist=False)
    created_by = relationship("User", foreign_keys=[created_by_admin_id])
