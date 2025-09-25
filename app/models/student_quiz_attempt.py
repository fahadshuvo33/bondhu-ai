from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models._base import BaseModel
from enum import Enum


class AttemptStatus(str, Enum):
    STARTED = "started"
    SUBMITTED = "submitted"
    GRADED = "graded"
    REVIEWED = "reviewed"


class StudentQuizAttempt(BaseModel):
    """Records a student's attempt at a quiz or mock exam."""

    __tablename__ = "student_quiz_attempts"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.user_id"), index=True)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), index=True)
    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id"), nullable=True)

    # Attempt details
    attempt_number = Column(Integer, default=1)
    status = Column(String, default=AttemptStatus.STARTED)
    score = Column(Float, nullable=True)
    total_marks_available = Column(Float, nullable=True)
    percentage_score = Column(Float, nullable=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)

    # Performance
    time_taken_minutes = Column(Integer, nullable=True)
    is_passed = Column(Boolean, nullable=True)
    
    # AI-generated feedback
    ai_overall_feedback = Column(Text, nullable=True)
    ai_recommendations = Column(Text, nullable=True) # JSON array of topics to review

    # Relationships
    student = relationship("Student", backref="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")
    classroom = relationship("Classroom")
    question_attempts = relationship("QuestionAttempt", back_populates="quiz_attempt", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("student_id", "quiz_id", "attempt_number", name="uq_student_quiz_attempt"),
    )


class QuestionAttempt(BaseModel):
    """Records a student's answer to a specific question within a quiz attempt."""

    __tablename__ = "question_attempts"

    quiz_attempt_id = Column(UUID(as_uuid=True), ForeignKey("student_quiz_attempts.id"), index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), index=True)
    
    # Student's answer
    student_answer = Column(Text, nullable=True)
    
    # Scoring
    marks_obtained = Column(Float, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    
    # AI feedback
    ai_feedback = Column(Text, nullable=True)
    ai_score_reasoning = Column(Text, nullable=True)

    # Timestamps
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    quiz_attempt = relationship("StudentQuizAttempt", back_populates="question_attempts")
    question = relationship("Question")

    __table_args__ = (
        UniqueConstraint("quiz_attempt_id", "question_id", name="uq_question_attempt"),
    )
