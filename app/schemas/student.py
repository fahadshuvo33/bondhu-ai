# schemas/student.py
from pydantic import BaseModel, Field, Optional,EmailStr
from datetime import datetime
from uuid import UUID

class StudentBase(BaseModel):
    """Base student schema"""
    student_id: Optional[str] = None
    grade_level: Optional[str] = None
    institution: Optional[str] = None
    institution_type: Optional[str] = Field(None, regex='^(school|college|university)$')
    department: Optional[str] = None
    section: Optional[str] = None
    academic_year: Optional[str] = None
    current_gpa: Optional[str] = None
    rank_in_class: Optional[int] = None
    study_hours_per_day: Optional[int] = Field(None, ge=0, le=24)
    preferred_study_time: Optional[str] = Field(
        None, 
        regex='^(morning|afternoon|evening|night)$'
    )
    learning_style: Optional[str] = Field(
        None,
        regex='^(visual|auditory|reading|kinesthetic)$'
    )
    
    class Config:
        orm_mode = True


class StudentCreate(StudentBase):
    """Schema for creating student profile"""
    parent_email: Optional[EmailStr] = None  # To link parent if minor
    is_minor: bool = False


class StudentUpdate(StudentBase):
    """Schema for updating student profile"""
    pass


class StudentResponse(StudentBase):
    """Student response with privacy applied"""
    id: UUID
    user_id: UUID
    is_minor: bool
    parent_consent: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True


class StudentPublicResponse(BaseModel):
    """Public student profile respecting privacy"""
    id: UUID
    user_id: UUID
    grade_level: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    learning_style: Optional[str] = None
    
    class Config:
        orm_mode = True