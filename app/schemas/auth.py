from pydantic import BaseModel, EmailStr, Field, validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AuthProvider(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    APPLE = "apple"


class AuthMethodBase(BaseModel):
    provider: AuthProvider
    identifier: str
    is_primary: bool = False
    is_verified: bool = False


class AuthMethod(AuthMethodBase):
    id: int
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RegisterBase(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    password: Optional[str] = Field(None, min_length=6)


class RegisterWithEmail(RegisterBase):
    email: EmailStr

    @model_validator(mode="after")
    def validate_password_required(self):
        if not self.password:
            raise ValueError("Password is required for email registration")
        return self


class RegisterWithPhone(RegisterBase):
    phone_number: str = Field(..., min_length=11, max_length=15)

    @validator("phone_number")
    def validate_phone_number(cls, v):
        import re

        if not re.match(r"^\+?880[0-9]{10}$", v.replace(" ", "")):
            raise ValueError("Invalid Bangladesh phone number")
        return v.replace(" ", "")


class RegisterWithGoogle(BaseModel):
    id_token: str
    # Google provides email, full_name, avatar_url


class LoginBase(BaseModel):
    pass


class LoginWithEmail(LoginBase):
    email: EmailStr
    password: str


class LoginWithPhone(LoginBase):
    phone_number: str
    password: Optional[str] = None  # Optional for OTP login

    @validator("phone_number")
    def validate_phone_number(cls, v):
        import re

        if not re.match(r"^\+?880[0-9]{10}$", v.replace(" ", "")):
            raise ValueError("Invalid Bangladesh phone number")
        return v.replace(" ", "")


class LoginWithGoogle(LoginBase):
    id_token: str


class OTPRequest(BaseModel):
    identifier: str  # email or phone
    purpose: str = Field(..., pattern="^(login|register|reset_password|add_method)$")

    @validator("identifier")
    def validate_identifier(cls, v):
        # Check if it's email
        if "@" in v:
            from pydantic import EmailStr

            EmailStr._validate(v)
        else:
            # Check if it's phone
            import re

            if not re.match(r"^\+?880[0-9]{10}$", v.replace(" ", "")):
                raise ValueError("Invalid email or phone number")
        return v


class OTPVerify(BaseModel):
    identifier: str
    otp_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    purpose: str


class AddAuthMethod(BaseModel):
    provider: AuthProvider
    identifier: Optional[str] = None  # For email/phone
    password: Optional[str] = None  # For email/phone with password
    id_token: Optional[str] = None  # For social auth

    @model_validator(mode="after")
    def validate_fields(self):
        if self.provider in [AuthProvider.EMAIL, AuthProvider.PHONE]:
            if not self.identifier:
                raise ValueError(f"{self.provider} requires identifier")
            if self.provider == AuthProvider.EMAIL and not self.password:
                raise ValueError("Email auth requires password")
        elif self.provider in [AuthProvider.GOOGLE, AuthProvider.FACEBOOK]:
            if not self.id_token:
                raise ValueError(f"{self.provider} requires id_token")
        return self


class RemoveAuthMethod(BaseModel):
    provider: AuthProvider
    identifier: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int  # user_id
    exp: datetime
    iat: datetime
    type: str  # access or refresh
    jti: Optional[str] = None  # JWT ID for refresh tokens

    # Session info
    auth_method: Optional[str] = None
    session_id: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserWithAuthInfo(BaseModel):
    id: int
    email: Optional[str] = None
    phone_number: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

    is_active: bool
    is_email_verified: bool
    is_phone_verified: bool

    auth_methods: List[AuthMethod]

    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionInfo(BaseModel):
    id: int
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    last_activity_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class UserSessions(BaseModel):
    current_session: SessionInfo
    other_sessions: List[SessionInfo]
    total_sessions: int
