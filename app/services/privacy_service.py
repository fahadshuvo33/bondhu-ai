# services/privacy_service.py - Dynamic privacy service
from typing import Optional, Dict, Any, Set
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.user_privacy import UserPrivacySettings
import json


class PrivacyService:
    """Dynamic privacy service"""
    
    # Fields that should never be exposed publicly
    ALWAYS_PRIVATE_FIELDS = {
        'hashed_password', 'password_reset_token', 'two_factor_secret',
        'verification_token', 'api_keys', 'internal_notes'
    }
    
    # Fields that are always public (even in locked profiles)
    ALWAYS_PUBLIC_FIELDS = {
        'id', 'username', 'user_type', 'created_at'
    }
    
    @staticmethod
    def get_visible_fields(
        viewer: Optional[User],
        target_user: User,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dynamically filter data based on privacy settings"""
        
        # User viewing their own profile sees everything
        if viewer and viewer.id == target_user.id:
            return {k: v for k, v in data.items() 
                    if k not in PrivacyService.ALWAYS_PRIVATE_FIELDS}
        
        privacy_settings = target_user.privacy_settings
        if not privacy_settings:
            # Default behavior if no privacy settings
            return PrivacyService._apply_default_privacy(data)
        
        # Handle locked profile
        if privacy_settings.profile_visibility == 'locked':
            return {k: v for k, v in data.items() 
                    if k in PrivacyService.ALWAYS_PUBLIC_FIELDS}
        
        # Get field visibility settings
        field_visibility = privacy_settings.field_visibility or {}
        default_visibility = privacy_settings.default_field_visibility
        
        filtered_data = {}
        
        for field, value in data.items():
            # Skip always private fields
            if field in PrivacyService.ALWAYS_PRIVATE_FIELDS:
                continue
                
            # Always include public fields
            if field in PrivacyService.ALWAYS_PUBLIC_FIELDS:
                filtered_data[field] = value
                continue
            
            # Check field-specific visibility
            is_visible = field_visibility.get(field, default_visibility)
            
            if is_visible:
                filtered_data[field] = value
        
        return filtered_data
    
    @staticmethod
    def _apply_default_privacy(data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default privacy rules when no settings exist"""
        from schemas.privacy import DEFAULT_FIELD_VISIBILITY
        
        filtered_data = {}
        for field, value in data.items():
            if field in PrivacyService.ALWAYS_PRIVATE_FIELDS:
                continue
            if field in PrivacyService.ALWAYS_PUBLIC_FIELDS:
                filtered_data[field] = value
                continue
            
            # Use default visibility or True if not specified
            if DEFAULT_FIELD_VISIBILITY.get(field, True):
                filtered_data[field] = value
        
        return filtered_data
    
    @staticmethod
    def merge_model_data(
        user: User,
        include_profile: bool = True,
        include_type_specific: bool = True
    ) -> Dict[str, Any]:
        """Merge data from user and related models"""
        data = {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'phone_number': user.phone_number,
            'user_type': user.user_type,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'created_at': user.created_at,
            'last_login_at': user.last_login_at,
        }
        
        # Add profile data if exists
        if include_profile and user.profile:
            profile_data = {
                'full_name': user.profile.full_name,
                'date_of_birth': user.profile.date_of_birth,
                'gender': user.profile.gender,
                'address': user.profile.address,
                'city': user.profile.city,
                'district': user.profile.district,
                'bio': user.profile.bio,
                'avatar_url': user.profile.avatar_url,
            }
            data.update(profile_data)
        
        # Add type-specific data
        if include_type_specific:
            if user.user_type == 'student' and user.student:
                student_data = {
                    'student_id': user.student.student_id,
                    'grade_level': user.student.grade_level,
                    'institution': user.student.institution,
                    'department': user.student.department,
                    'current_gpa': user.student.current_gpa,
                    'learning_style': user.student.learning_style,
                }
                data.update(student_data)
            
            elif user.user_type == 'teacher' and user.teacher:
                teacher_data = {
                    'employee_id': user.teacher.employee_id,
                    'designation': user.teacher.designation,
                    'institution': user.teacher.institution,
                    'department': user.teacher.department,
                    'specializations': user.teacher.specializations,
                    'years_of_experience': user.teacher.years_of_experience,
                    'is_verified': user.teacher.is_verified,
                }
                data.update(teacher_data)
            
            # Add other user types...
        
        return data