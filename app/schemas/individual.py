# schemas/individual.py (continued)
from pydantic import BaseModel, Field, Optional
from datetime import datetime
from uuid import UUID


class IndividualBase(BaseModel):
    """Base individual schema"""
    learning_purpose: Optional[str] = Field(
        None,
        regex='^(research|university|job_prep|personal)$'
    )
    occupation: Optional[str] = None
    organization: Optional[str] = None
    highest_education: Optional[str] = None
    field_of_study: Optional[str] = None
    years_of_experience: Optional[int] = Field(None, ge=0)
    areas_of_interest: Optional[list[str]] = []
    learning_goals: Optional[list[str]] = []
    preferred_learning_style: Optional[str] = Field(
        None,
        regex='^(visual|auditory|reading)$'
    )
    primary_use_case: Optional[str] = None
    preferred_ai_model: Optional[str] = None
    needs_citations: bool = False
    needs_latex_support: bool = False
    needs_code_support: bool = False
    
    class Config:
        orm_mode = True


class IndividualCreate(IndividualBase):
    """Create individual profile"""
    referral_source: Optional[str] = None
    subscription_reason: Optional[str] = None


class IndividualUpdate(IndividualBase):
    """Update individual profile"""
    pass


class IndividualResponse(IndividualBase):
    """Individual response"""
    id: UUID
    user_id: UUID
    total_study_hours: int
    total_documents_studied: int
    achievement_points: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True
