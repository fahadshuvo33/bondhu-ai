from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models._base import BaseModel
from enum import Enum


class UserRoleStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"  # For role requests


class UserRole(BaseModel):
    """Track all roles a user has (for role switching)"""

    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    role_type = Column(String, nullable=False)  # student, teacher, parent, admin
    status = Column(String, default=UserRoleStatus.ACTIVE)

    # Which role-specific profile to link to
    profile_id = Column(UUID(as_uuid=True), nullable=True)  # ID from respective table

    # Is this the currently active role?
    is_current = Column(Boolean, default=False)

    # When was this role last used?
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Verification for teacher/admin roles
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by_admin_id = Column(UUID(as_uuid=True), nullable=True)

    # Approval
    requested_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_admin_id = Column(UUID(as_uuid=True), nullable=True)

    # Ensure one role type per user
    __table_args__ = (UniqueConstraint("user_id", "role_type", name="uq_user_role"),)

    # Relationships
    user = relationship("User", backref="roles")
