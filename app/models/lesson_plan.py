from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, DateTime, UniqueConstraint, Enum as SQLEnum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models._base import BaseModel
from enum import Enum


class LessonPlanStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class LessonPlan(BaseModel):
    """Teachers can create lesson plans."""

    __tablename__ = "lesson_plans"

    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.user_id"), index=True)
    classroom_id = Column(
        UUID(as_uuid=True), ForeignKey("classrooms.id"), nullable=True, index=True
    )

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(LessonPlanStatus), default=LessonPlanStatus.DRAFT)
    grade_level = Column(String, nullable=True)
    subject = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=True)

    # Content of the lesson plan
    learning_objectives = Column(Text, nullable=True)  # JSON array
    materials_needed = Column(Text, nullable=True)  # JSON array
    activities = Column(Text, nullable=True)  # JSON array of steps/descriptions
    assessment_methods = Column(Text, nullable=True)  # JSON array

    # AI-generated content
    ai_generated = Column(Boolean, default=False)
    ai_generation_prompt = Column(Text, nullable=True)
    ai_model_used = Column(String, nullable=True)

    # Publishing details
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    teacher = relationship("Teacher", backref="lesson_plans")
    classroom = relationship("Classroom", backref="lesson_plans")
    assignments = relationship(
        "Assignment", back_populates="lesson_plan", cascade="all, delete-orphan"
    )


class AssignmentType(str, Enum):
    HOMEWORK = "homework"
    QUIZ = "quiz"  # Linked to a Quiz model
    PROJECT = "project"
    ESSAY = "essay"


class Assignment(BaseModel):
    """Assignments created by teachers, linked to lesson plans or study materials."""

    __tablename__ = "assignments"

    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.user_id"), index=True)
    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id"), index=True)
    lesson_plan_id = Column(
        UUID(as_uuid=True), ForeignKey("lesson_plans.id"), nullable=True, index=True
    )
    study_material_id = Column(
        UUID(as_uuid=True), ForeignKey("study_materials.id"), nullable=True, index=True
    )

    # Assignment details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    assignment_type = Column(SQLEnum(AssignmentType), default=AssignmentType.HOMEWORK)
    due_date = Column(DateTime(timezone=True), nullable=False)
    total_marks = Column(Float, nullable=True)

    # Submission settings
    allow_late_submissions = Column(Boolean, default=False)
    late_submission_penalty = Column(Float, default=0.0)
    max_file_size_mb = Column(Integer, default=10)
    allowed_file_types = Column(Text, nullable=True)  # JSON array: ["pdf", "docx"]

    # AI settings
    ai_auto_grade = Column(Boolean, default=False)
    ai_grading_rubric = Column(Text, nullable=True)  # JSON
    ai_feedback_enabled = Column(Boolean, default=False)

    # Link to Quiz if assignment type is QUIZ
    quiz_id = Column(
        UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=True, unique=True
    )

    # Relationships
    teacher = relationship("Teacher", backref="assignments")
    classroom = relationship("Classroom", backref="assignments")
    lesson_plan = relationship("LessonPlan", back_populates="assignments")
    study_material = relationship("StudyMaterial", backref="assignments")
    quiz = relationship("Quiz", backref="assignment", uselist=False)
    submissions = relationship(
        "StudentAssignment", back_populates="assignment", cascade="all, delete-orphan"
    )


class StudentAssignment(BaseModel):
    """Tracks student submissions for assignments."""

    __tablename__ = "student_assignments"

    student_id = Column(UUID(as_uuid=True), ForeignKey("students.user_id"), index=True)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.id"), index=True)

    # Submission details
    submission_text = Column(Text, nullable=True)
    submission_url = Column(String, nullable=True)  # For file uploads
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    is_late = Column(Boolean, default=False)

    # Grading
    grade = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    graded_by_teacher_id = Column(
        UUID(as_uuid=True), ForeignKey("teachers.user_id"), nullable=True
    )
    graded_at = Column(DateTime(timezone=True), nullable=True)

    # AI grading
    ai_graded = Column(Boolean, default=False)
    ai_grade_details = Column(Text, nullable=True)  # JSON for AI's breakdown
    ai_feedback = Column(Text, nullable=True)

    # Relationships
    student = relationship("Student", backref="submissions")
    assignment = relationship("Assignment", back_populates="submissions")
    grader = relationship("Teacher", foreign_keys=[graded_by_teacher_id])

    __table_args__ = (
        UniqueConstraint("student_id", "assignment_id", name="uq_student_assignment"),
    )
