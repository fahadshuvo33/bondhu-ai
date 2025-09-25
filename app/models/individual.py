# individual.py
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models._base import BaseModel


class Individual(BaseModel):
    """Individual user - not part of classroom system, for personal learning"""
    
    __tablename__ = "individuals"
    
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True
    )
    
    # Learning purpose
    learning_purpose = Column(String, nullable=True)  # research, university, job_prep, personal
    occupation = Column(String, nullable=True)  # current occupation/profession
    organization = Column(String, nullable=True)  # company/university name
    
    # Academic/Professional background
    highest_education = Column(String, nullable=True)  # PhD, Masters, Bachelors, etc.
    field_of_study = Column(String, nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    
    # Learning preferences
    areas_of_interest = Column(Text, nullable=True)  # JSON array of topics
    learning_goals = Column(Text, nullable=True)  # JSON array of goals
    preferred_learning_style = Column(String, nullable=True)  # visual, auditory, reading
    
    # Usage patterns
    primary_use_case = Column(String, nullable=True)  # research_paper, exam_prep, skill_learning
    preferred_study_time = Column(String, nullable=True)  # morning, afternoon, evening, night
    
    # AI preferences
    preferred_ai_model = Column(String, nullable=True)  # gpt-4, gpt-3.5, claude
    preferred_response_style = Column(String, nullable=True)  # detailed, concise, academic
    
    # Content preferences
    preferred_content_language = Column(String, default="en")  # en, bn, mixed
    preferred_difficulty_level = Column(String, nullable=True)  # beginner, intermediate, advanced
    
    # Professional features
    needs_citations = Column(Boolean, default=False)  # for research work
    needs_latex_support = Column(Boolean, default=False)  # for academic writing
    needs_code_support = Column(Boolean, default=False)  # for programming
    
    # Privacy settings
    allow_data_for_improvement = Column(Boolean, default=True)
    share_learning_progress = Column(Boolean, default=False)
    
    # Subscription tracking
    subscription_reason = Column(Text, nullable=True)  # why they subscribed
    referral_source = Column(String, nullable=True)  # how they found the platform
    
    # Usage statistics
    total_study_hours = Column(Integer, default=0)
    total_documents_studied = Column(Integer, default=0)
    favorite_topics = Column(Text, nullable=True)  # JSON array based on usage
    
    # Certification/Badge support (for gamification)
    earned_certificates = Column(Text, nullable=True)  # JSON array
    achievement_points = Column(Integer, default=0)
    
    # Notes and personal knowledge base
    enable_personal_notes = Column(Boolean, default=True)
    enable_knowledge_graph = Column(Boolean, default=False)  # premium feature
    
    # Relationships
    user = relationship("User", backref="individual", uselist=False)