# models/user_privacy.py - Dynamic privacy settings
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SQLEnum, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models._base import BaseModel
from enum import Enum


class ProfileVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"  # Only connections can see
    LOCKED = "locked"   # Only username visible


class UserPrivacySettings(BaseModel):
    """Dynamic privacy settings using JSON for flexibility"""
    
    __tablename__ = "user_privacy_settings"
    
    # One-to-one relationship with User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Overall profile visibility
    profile_visibility = Column(
        SQLEnum(ProfileVisibility), 
        nullable=False, 
        default=ProfileVisibility.PUBLIC
    )
    
    # Dynamic field visibility settings stored as JSON
    # Format: {"field_name": boolean, ...}
    field_visibility = Column(JSON, nullable=False, default={})
    
    # Search & Discovery
    search_visibility = Column(JSON, nullable=False, default={
        "searchable_by_email": False,
        "searchable_by_phone": False,
        "searchable_by_username": True,
        "searchable_by_name": True,
        "appear_in_suggestions": True,
        "appear_in_directory": True
    })
    
    # Communication settings
    communication_settings = Column(JSON, nullable=False, default={
        "allow_messages_from": "everyone",  # everyone, connections, nobody
        "allow_connection_requests": True,
        "allow_mentions": True,
        "allow_classroom_invites": True
    })
    
    # Default visibility for new fields (when model changes)
    default_field_visibility = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="privacy_settings", uselist=False)