# schemas/privacy.py - Dynamic privacy schemas
from typing import Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime


class ProfileVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    LOCKED = "locked"


# Default visibility settings for different field types
DEFAULT_FIELD_VISIBILITY = {
    # Sensitive fields default to private
    "email": False,
    "phone_number": False,
    "date_of_birth": False,
    "address": False,
    "nid_number": False,
    "student_id": False,
    "employee_id": False,
    "current_gpa": False,
    "rank_in_class": False,
    "parent_user_id": False,
    
    # Public fields by default
    "full_name": True,
    "username": True,
    "bio": True,
    "avatar_url": True,
    "city": True,
    "institution": True,
    "designation": True,
    "specializations": True,
    "is_verified": True,
}


class FieldVisibilityUpdate(BaseModel):
    """Update visibility for specific fields"""
    fields: Dict[str, bool] = Field(..., example={
        "email": False,
        "full_name": True,
        "institution": True
    })
    
    @validator('fields')
    def validate_fields(cls, v):
        # You can add validation to ensure field names are valid
        return v


class SearchVisibilitySettings(BaseModel):
    """Search and discovery settings"""
    searchable_by_email: bool = False
    searchable_by_phone: bool = False
    searchable_by_username: bool = True
    searchable_by_name: bool = True
    appear_in_suggestions: bool = True
    appear_in_directory: bool = True


class CommunicationSettings(BaseModel):
    """Communication preferences"""
    allow_messages_from: str = Field(
        default="everyone",
        regex="^(everyone|connections|nobody)$"
    )
    allow_connection_requests: bool = True
    allow_mentions: bool = True
    allow_classroom_invites: bool = True


class PrivacySettingsBase(BaseModel):
    """Base privacy settings"""
    profile_visibility: ProfileVisibility = ProfileVisibility.PUBLIC
    default_field_visibility: bool = True
    
    class Config:
        orm_mode = True
        use_enum_values = True


class PrivacySettingsCreate(PrivacySettingsBase):
    """Create privacy settings with defaults"""
    field_visibility: Optional[Dict[str, bool]] = None
    search_visibility: Optional[SearchVisibilitySettings] = None
    communication_settings: Optional[CommunicationSettings] = None
    
    @validator('field_visibility', pre=True, always=True)
    def set_default_field_visibility(cls, v):
        if v is None:
            return DEFAULT_FIELD_VISIBILITY.copy()
        # Merge with defaults
        defaults = DEFAULT_FIELD_VISIBILITY.copy()
        defaults.update(v)
        return defaults


class PrivacySettingsUpdate(BaseModel):
    """Update privacy settings"""
    profile_visibility: Optional[ProfileVisibility] = None
    default_field_visibility: Optional[bool] = None
    field_visibility: Optional[Dict[str, bool]] = None
    search_visibility: Optional[Dict[str, Any]] = None
    communication_settings: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True


class PrivacySettingsResponse(PrivacySettingsBase):
    """Privacy settings response"""
    id: UUID
    user_id: UUID
    field_visibility: Dict[str, bool]
    search_visibility: Dict[str, Any]
    communication_settings: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True