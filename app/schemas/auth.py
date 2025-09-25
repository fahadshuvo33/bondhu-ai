# schemas/auth.py
from datetime import datetime
from typing import Optional, Union, Literal
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from enum import Enum


class UserType(str, Enum):
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    ADMIN = "admin"
    INDIVIDUAL = "individual"


class AuthMethod(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    USERNAME = "username"


# Registration Schemas
class UserRegisterBase(BaseModel):
    """Base registration schema"""
    user_type: UserType
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, regex=r'^\+?[1-9]\d{1,14}$')
    username: Optional[str] = Field(None, min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_-]+$')
    password: str = Field(..., min_length=8, max_length=100)
    
    # Profile info
    full_name: str = Field(..., min_length=2, max_length=100)
    preferred_language: Literal["en", "bn"] = "en"
    timezone: str = "Asia/Dhaka"
    
    @root_validator
    def validate_identifier(cls, values):
        """Ensure at least one identifier is provided"""
        email = values.get('email')
        phone = values.get('phone_number')
        username = values.get('username')
        
        if not any([email, phone, username]):
            raise ValueError('At least one identifier (email, phone_number, or username) must be provided')
        
        return values
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class StudentRegister(UserRegisterBase):
    """Student registration schema"""
    # Student specific fields
    grade_level: str = Field(..., min_length=1, max_length=50)
    institution: str = Field(..., min_length=2, max_length=200)
    institution_type: Literal["school", "college", "university"]
    date_of_birth: datetime
    
    # Parent info if minor
    is_minor: bool = False
    parent_email: Optional[EmailStr] = None
    parent_phone: Optional[str] = None
    
    @root_validator
    def validate_minor_requirements(cls, values):
        """Validate minor requirements"""
        is_minor = values.get('is_minor')
        parent_email = values.get('parent_email')
        parent_phone = values.get('parent_phone')
        dob = values.get('date_of_birth')
        
        # Auto-detect minor based on age
        if dob:
            age = (datetime.now() - dob).days / 365.25
            if age < 18:
                values['is_minor'] = True
        
        # Require parent info for minors
        if values.get('is_minor') and not (parent_email or parent_phone):
            raise ValueError('Parent email or phone is required for minor students')
        
        return values


class TeacherRegister(UserRegisterBase):
    """Teacher registration schema"""
    # Required teacher fields
    institution: str = Field(..., min_length=2, max_length=200)
    institution_type: Literal["school", "college", "university"]
    designation: str = Field(..., min_length=2, max_length=100)
    employee_id: Optional[str] = None
    
    # Optional verification
    highest_degree: Optional[str] = None
    specializations: Optional[list[str]] = []
    years_of_experience: Optional[int] = Field(None, ge=0)
    verification_document: Optional[str] = None  # Base64 or URL


class ParentRegister(UserRegisterBase):
    """Parent registration schema"""
    # Optional parent fields
    occupation: Optional[str] = None
    nid_number: Optional[str] = None
    
    # Children to link (optional during registration)
    children_identifiers: Optional[list[dict]] = Field(None, description="List of children's email/phone/username")


class IndividualRegister(UserRegisterBase):
    """Individual registration schema"""
    learning_purpose: Literal["research", "university", "job_prep", "personal"]
    occupation: Optional[str] = None
    organization: Optional[str] = None


class AdminRegister(UserRegisterBase):
    """Admin registration schema (only by super admin)"""
    employee_id: str = Field(..., min_length=3, max_length=50)
    admin_role: Literal["admin", "moderator", "support", "content_manager"]
    department: Optional[str] = None


# Login Schemas
class UserLogin(BaseModel):
    """Login schema supporting multiple identifiers"""
    identifier: str = Field(..., description="Email, phone number, or username")
    password: str
    remember_me: bool = False
    
    @validator('identifier')
    def validate_identifier(cls, v):
        """Basic validation for identifier"""
        if not v or len(v) < 3:
            raise ValueError('Invalid identifier')
        return v.strip().lower()


class TwoFactorVerify(BaseModel):
    """Two-factor authentication verification"""
    code: str = Field(..., regex=r'^\d{6}$')
    token: str = Field(..., description="Temporary token from login")


# Response Schemas
class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 3600


class LoginResponse(BaseModel):
    """Login response with user info and tokens"""
    user: dict  # Simplified user data
    tokens: TokenResponse
    requires_2fa: bool = False
    temp_token: Optional[str] = None  # For 2FA flow


class RegisterResponse(BaseModel):
    """Registration response"""
    user: dict
    tokens: TokenResponse
    requires_verification: bool = True
    verification_sent_to: Optional[str] = None