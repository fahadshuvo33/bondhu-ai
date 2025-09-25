from pydantic import BaseModel, Field, Optional
from datetime import datetime
from uuid import UUID


# schemas/teacher.py
class TeacherBase(BaseModel):
    """Base teacher schema"""
    employee_id: Optional[str] = None
    designation: Optional[str] = None
    institution: str
    institution_type: Optional[str] = Field(None, regex='^(school|college|university)$')
    department: Optional[str] = None
    highest_degree: Optional[str] = None
    specializations: Optional[list[str]] = []
    years_of_experience: Optional[int] = Field(None, ge=0)
    teaching_subjects: Optional[list[str]] = []
    grade_levels: Optional[list[str]] = []
    is_available_for_questions: bool = True
    consultation_rate_per_hour: Optional[int] = Field(None, ge=0)
    office_hours: Optional[dict] = None
    
    class Config:
        orm_mode = True


class TeacherCreate(TeacherBase):
    """Schema for creating teacher profile"""
    verification_document: Optional[str] = None  # Document for verification


class TeacherUpdate(BaseModel):
    """Schema for updating teacher profile"""
    designation: Optional[str] = None
    department: Optional[str] = None
    highest_degree: Optional[str] = None
    specializations: Optional[list[str]] = None
    years_of_experience: Optional[int] = Field(None, ge=0)
    teaching_subjects: Optional[list[str]] = None
    grade_levels: Optional[list[str]] = None
    is_available_for_questions: Optional[bool] = None
    consultation_rate_per_hour: Optional[int] = Field(None, ge=0)
    office_hours: Optional[dict] = None
    
    class Config:
        orm_mode = True


class TeacherResponse(TeacherBase):
    """Teacher response"""
    id: UUID
    user_id: UUID
    is_verified: bool
    verified_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True


class TeacherPublicResponse(BaseModel):
    """Public teacher profile"""
    id: UUID
    user_id: UUID
    designation: Optional[str]
    institution: str
    department: Optional[str]
    specializations: Optional[list[str]]
    teaching_subjects: Optional[list[str]]
    years_of_experience: Optional[int]
    is_verified: bool
    is_available_for_questions: bool
    consultation_rate_per_hour: Optional[int]
    
    class Config:
        orm_mode = True