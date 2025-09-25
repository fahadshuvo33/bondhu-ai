from pydantic import BaseModel, Field, Optional
from datetime import datetime
from uuid import UUID
from app.schemas.base import BaseSchema
from email_validator import EmailStr

# schemas/parent.py

class ParentBase(BaseModel):
    """Base parent schema"""
    occupation: Optional[str] = None
    nid_number: Optional[str] = None
    notify_on_child_activity: bool = True
    notify_on_low_credits: bool = True
    notify_weekly_report: bool = True
    notify_on_grade_update: bool = True
    monitor_chat_content: bool = False
    monitor_study_materials: bool = True
    require_approval_for_ai_models: bool = False
    monthly_credit_limit: Optional[int] = Field(None, ge=0)
    require_approval_above_credits: Optional[int] = Field(None, ge=0)
    
    class Config:
        orm_mode = True


class ParentCreate(ParentBase):
    """Schema for creating parent profile"""
    children_emails: Optional[list[EmailStr]] = []  # To link children


class ParentUpdate(BaseModel):
    """Schema for updating parent profile"""
    occupation: Optional[str] = None
    notify_on_child_activity: Optional[bool] = None
    notify_on_low_credits: Optional[bool] = None
    notify_weekly_report: Optional[bool] = None
    notify_on_grade_update: Optional[bool] = None
    monitor_chat_content: Optional[bool] = None
    monitor_study_materials: Optional[bool] = None
    require_approval_for_ai_models: Optional[bool] = None
    monthly_credit_limit: Optional[int] = Field(None, ge=0)
    require_approval_above_credits: Optional[int] = Field(None, ge=0)
    
    class Config:
        orm_mode = True
