# schemas/profile.py - Common Profile Schema
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class ProfileBase(BaseModel):
    """Base profile schema"""
    full_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(None, regex='^(male|female|other|prefer_not_to_say)$')
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    postal_code: Optional[str] = None
    preferred_language: str = Field(default="en", regex='^(en|bn)$')
    timezone: str = Field(default="Asia/Dhaka")
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    
    class Config:
        orm_mode = True


class ProfileCreate(ProfileBase):
    """Schema for creating profile"""
    pass


class ProfileUpdate(BaseModel):
    """Schema for updating profile"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(None, regex='^(male|female|other|prefer_not_to_say)$')
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    postal_code: Optional[str] = None
    preferred_language: Optional[str] = Field(None, regex='^(en|bn)$')
    timezone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    
    class Config:
        orm_mode = True


class ProfileResponse(ProfileBase):
    """Profile response with privacy applied"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True








from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field, create_model
from uuid import UUID
from datetime import datetime


class DynamicProfileResponse(BaseModel):
    """Base class for dynamic profile responses"""
    
    @classmethod
    def create_from_data(cls, data: Dict[str, Any]):
        """Create a dynamic model instance from filtered data"""
        # Create dynamic field definitions
        fields = {}
        for key, value in data.items():
            if value is None:
                fields[key] = (Optional[type(value)], None)
            else:
                fields[key] = (type(value), ...)
        
        # Create dynamic model
        DynamicModel = create_model('DynamicProfile', **fields)
        return DynamicModel(**data)


class UnifiedPublicProfile(BaseModel):
    """Unified public profile that adapts based on privacy settings"""
    # Always visible fields
    id: UUID
    username: Optional[str]
    user_type: str
    created_at: datetime
    profile_visibility: str
    
    # Dynamic fields (added based on privacy settings)
    additional_fields: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        orm_mode = True


class UnifiedProfileResponse(BaseModel):
    """Complete unified profile response"""
    # Core user fields
    id: UUID
    username: Optional[str]
    email: Optional[str]
    user_type: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    
    # Profile data (dynamically included)
    profile: Optional[Dict[str, Any]]
    
    # Type-specific data (student/teacher/parent/individual)
    type_specific_data: Optional[Dict[str, Any]]
    
    # Privacy settings (only for own profile)
    privacy_settings: Optional[Dict[str, Any]]
    
    class Config:
        orm_mode = True


# schemas/profile_builder.py - Helper to build profiles dynamically
class ProfileBuilder:
    """Helper class to build profiles with privacy applied"""
    
    @staticmethod
    def build_public_profile(
        user_data: Dict[str, Any],
        viewer_permissions: Dict[str, bool]
    ) -> Dict[str, Any]:
        """Build public profile based on permissions"""
        public_data = {}
        
        for field, value in user_data.items():
            if viewer_permissions.get(field, False):
                public_data[field] = value
        
        return public_data
    
    @staticmethod
    def build_search_result(
        user: Any,
        privacy_service: Any
    ) -> Dict[str, Any]:
        """Build search result with minimal info"""
        # Always show basic info
        result = {
            'id': str(user.id),
            'username': user.username,
            'user_type': user.user_type,
            'is_verified': user.is_verified if hasattr(user, 'is_verified') else False,
        }
        
        # Add additional fields based on privacy
        if user.privacy_settings:
            settings = user.privacy_settings
            if settings.profile_visibility != 'locked':
                # Add avatar and display name for non-locked profiles
                if hasattr(user, 'profile') and user.profile:
                    if settings.field_visibility.get('avatar_url', True):
                        result['avatar_url'] = user.profile.avatar_url
                    if settings.field_visibility.get('full_name', True):
                        result['display_name'] = user.profile.full_name
                
                # Add institution for teachers/students if allowed
                if user.user_type in ['teacher', 'student']:
                    type_model = getattr(user, user.user_type)
                    if type_model and settings.field_visibility.get('institution', True):
                        result['institution'] = type_model.institution
        
        return result