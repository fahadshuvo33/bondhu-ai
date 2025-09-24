from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ProgressReport(BaseModel):
    """Student progress reports for parents"""

    __tablename__ = "progress_reports"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.user_id"), index=True)

    # Report period
    report_type = Column(String)  # daily, weekly, monthly
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))

    # Study metrics
    total_study_time_minutes = Column(Integer, default=0)
    total_questions_asked = Column(Integer, default=0)
    total_pdfs_read = Column(Integer, default=0)

    # Performance metrics
    average_response_accuracy = Column(Float, nullable=True)  # 0-100%
    topics_covered = Column(Text, nullable=True)  # JSON array
    subjects_studied = Column(Text, nullable=True)  # JSON object with time per subject

    # AI usage
    ai_models_used = Column(Text, nullable=True)  # JSON object with usage count
    credits_spent = Column(Float, default=0)

    # Strengths and weaknesses
    strong_topics = Column(Text, nullable=True)  # JSON array
    weak_topics = Column(Text, nullable=True)  # JSON array

    # Teacher feedback (if any)
    teacher_feedback = Column(Text, nullable=True)

    # Parent viewed
    viewed_by_parent = Column(Boolean, default=False)
    viewed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="progress_reports")
