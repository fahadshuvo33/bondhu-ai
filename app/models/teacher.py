from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models._base import BaseModel


class Teacher(BaseModel):
    """Teacher-specific information"""

    __tablename__ = "teachers"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True
    )

    # Professional info
    employee_id = Column(String, nullable=True, index=True)
    designation = Column(String, nullable=True)  # Professor, Lecturer, Teacher
    institution = Column(String, nullable=False)
    institution_type = Column(String, nullable=True)  # school, college, university
    department = Column(String, nullable=True)

    # Qualifications
    highest_degree = Column(String, nullable=True)
    specializations = Column(Text, nullable=True)  # JSON array of subjects
    years_of_experience = Column(Integer, nullable=True)

    # Verification
    is_verified = Column(Boolean, default=False)
    verification_document_url = Column(String, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by_admin_id = Column(UUID(as_uuid=True), nullable=True)

    # Teaching preferences
    teaching_subjects = Column(Text, nullable=True)  # JSON array
    grade_levels = Column(Text, nullable=True)  # JSON array of grade levels they teach

    # Availability
    is_available_for_questions = Column(Boolean, default=True)
    consultation_rate_per_hour = Column(Integer, nullable=True)  # In credits
    office_hours = Column(Text, nullable=True)  # JSON schedule

    # Relationships
    user = relationship("User", backref="teacher", uselist=False)
    classrooms = relationship("Classroom", back_populates="teacher")
    announcements = relationship("Announcement", back_populates="teacher")
