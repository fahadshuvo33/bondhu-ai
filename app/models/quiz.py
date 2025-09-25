from sqlalchemy import Column, String, Integer, Text, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models._base import BaseModel
from enum import Enum


class QuizType(str, Enum):
    QUIZ = "quiz"
    MOCK_EXAM = "mock_exam"
    PRACTICE = "practice"
    ASSIGNMENT = "assignment"


class QuestionType(str, Enum):
    MCQ = "mcq"  # Multiple Choice Question
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    FILL_IN_THE_BLANK = "fill_in_the_blank"


class Quiz(BaseModel):
    """Represents a quiz or mock exam generated from study materials or syllabuses."""

    __tablename__ = "quizzes"

    # Creator/Owner
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    classroom_id = Column(
        UUID(as_uuid=True), ForeignKey("classrooms.id"), nullable=True
    )

    # Quiz details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    quiz_type = Column(String, default=QuizType.QUIZ)
    difficulty_level = Column(String, nullable=True)  # easy, medium, hard

    # Source material (either study_material or syllabus)
    study_material_id = Column(
        UUID(as_uuid=True), ForeignKey("study_materials.id"), nullable=True, index=True
    )
    syllabus_id = Column(
        UUID(as_uuid=True), ForeignKey("syllabuses.id"), nullable=True, index=True
    )

    # Settings
    total_marks = Column(Float, default=0.0)
    time_limit_minutes = Column(Integer, nullable=True)
    pass_percentage = Column(Float, default=0.0)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    available_from = Column(DateTime(timezone=True), nullable=True)
    available_to = Column(DateTime(timezone=True), nullable=True)
    show_answers_after_attempt = Column(Boolean, default=False)

    # AI-generated metadata
    ai_generated = Column(Boolean, default=True)
    ai_model_used = Column(String, nullable=True)
    ai_generation_settings = Column(Text, nullable=True)  # JSON for prompt, params

    # Relationships
    creator = relationship("User", backref="created_quizzes")
    classroom = relationship("Classroom", backref="quizzes")
    study_material = relationship("StudyMaterial", backref="quizzes")
    syllabus = relationship("Syllabus", backref="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("StudentQuizAttempt", back_populates="quiz")


class Question(BaseModel):
    """Individual questions belonging to a quiz."""

    __tablename__ = "questions"

    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), index=True)

    # Question details
    question_text = Column(Text, nullable=False)
    question_type = Column(String, default=QuestionType.MCQ)
    marks = Column(Float, default=0.0)
    difficulty = Column(String, nullable=True)  # easy, medium, hard

    # For MCQ/True-False
    options = Column(Text, nullable=True)  # JSON array of strings
    correct_answer = Column(Text, nullable=True)  # JSON array for multiple correct, or single string

    # For short answer/essay scoring
    ai_rubric = Column(Text, nullable=True)  # JSON for AI scoring guidelines
    keywords_for_scoring = Column(Text, nullable=True)  # JSON array of keywords

    # Source context
    source_chunk_id = Column(
        UUID(as_uuid=True), ForeignKey("document_chunk_masters.id"), nullable=True
    )
    source_page_number = Column(Integer, nullable=True)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    source_chunk = relationship("DocumentChunkMaster")
