from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Student(BaseModel):
    """Student-specific information"""

    __tablename__ = "students"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True
    )

    # Student specific
    student_id = Column(String, nullable=True, index=True)  # School/University ID
    grade_level = Column(String, nullable=True)  # Class 6-12, Year 1-4, etc
    institution = Column(String, nullable=True)
    institution_type = Column(String, nullable=True)  # school, college, university
    department = Column(String, nullable=True)  # For university students
    section = Column(String, nullable=True)  # For school students
    academic_year = Column(String, nullable=True)

    # Parent link (if minor)
    parent_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_minor = Column(Boolean, default=False)
    parent_consent = Column(Boolean, default=False)
    parent_consent_date = Column(DateTime(timezone=True), nullable=True)

    # Academic Performance
    current_gpa = Column(String, nullable=True)
    rank_in_class = Column(Integer, nullable=True)

    # Study preferences
    study_hours_per_day = Column(Integer, nullable=True)
    preferred_study_time = Column(
        String, nullable=True
    )  # morning, afternoon, evening, night
    learning_style = Column(
        String, nullable=True
    )  # visual, auditory, reading, kinesthetic

    # Parent control settings (for future)
    parent_control_enabled = Column(Boolean, default=False)
    restricted_features = Column(
        Text, nullable=True
    )  # JSON array of restricted features
    daily_time_limit_minutes = Column(Integer, nullable=True)
    allowed_time_slots = Column(Text, nullable=True)  # JSON array of time slots

    # Relationships
    user = relationship(
        "User", foreign_keys=[user_id], backref="student", uselist=False
    )
    parent = relationship("User", foreign_keys=[parent_user_id], backref="children")
    classrooms = relationship("ClassroomStudent", back_populates="student")
    study_materials = relationship("StudyMaterial", back_populates="student")
    chat_sessions = relationship("ChatSession", back_populates="student")
    progress_reports = relationship("ProgressReport", back_populates="student")
