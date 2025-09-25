# schemas/admin.py (continued)
from pydantic import BaseModel, Field, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

# schemas/admin.py

class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    SUPPORT = "support"
    CONTENT_MANAGER = "content_manager"


class AdminBase(BaseModel):
    """Base admin schema"""
    employee_id: str
    admin_role: AdminRole
    department: Optional[str] = None
    require_2fa: bool = True
    
    class Config:
        orm_mode = True
        use_enum_values = True


class AdminCreate(AdminBase):
    """Create admin"""
    permissions: Optional[list[str]] = []
    ip_whitelist: Optional[list[str]] = []


class AdminUpdate(BaseModel):
    """Update admin"""
    department: Optional[str] = None
    permissions: Optional[list[str]] = None
    ip_whitelist: Optional[list[str]] = None
    require_2fa: Optional[bool] = None
    
    class Config:
        orm_mode = True


class AdminResponse(AdminBase):
    """Admin response"""
    id: UUID
    user_id: UUID
    permissions: Optional[list[str]]
    last_activity_at: Optional[datetime]
    total_actions: int
    created_by_admin_id: Optional[UUID]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True
