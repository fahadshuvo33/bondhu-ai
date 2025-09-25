from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from pydantic import model_validator

from app.schemas.base import BaseSchema, TimestampMixin
from app.schemas.auth import AuthMethod


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v:
            import re

            if not re.match(r"^\+?880[0-9]{10}$", v.replace(" ", "")):
                raise ValueError("Invalid Bangladesh phone number")
            return v.replace(" ", "")
        return v

    @model_validator(mode="after")
    def validate_at_least_one_identifier(self):
        if not self.email and not self.phone_number:
            raise ValueError("At least one of email or phone_number must be provided")
        return self


class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=6)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    avatar_url: Optional[str] = None


class UserInDBBase(BaseModel, BaseSchema, TimestampMixin):
    id: int
    email: Optional[str] = None
    phone_number: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

    is_active: bool
    is_email_verified: bool
    is_phone_verified: bool

    last_login_at: Optional[datetime] = None


class User(UserInDBBase):
    pass


class UserWithCredits(UserInDBBase):
    credit_balance: float = 0.0


class UserWithAuthMethods(UserInDBBase):
    auth_methods: List[AuthMethod] = []


class UserProfile(UserInDBBase):
    credit_balance: float = 0.0
    auth_methods: List[AuthMethod] = []
    total_ai_requests: int = 0
    member_since_days: int = 0