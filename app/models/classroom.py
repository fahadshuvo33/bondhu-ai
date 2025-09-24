from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Text,
    ForeignKey,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models._base import BaseModel
from enum import Enum


class ClassroomRole(str, Enum):
    OWNER = "owner"  # Main teacher who created
    TEACHER = "teacher"  # Co-teachers
    ASSISTANT = "assistant"  # Teaching assistants


class Classroom(BaseModel):
    """Virtual classroom for teachers and students"""

    __tablename__ = "classrooms"

    # Basic info
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)  # Join code
    description = Column(Text, nullable=True)
    subject = Column(String, nullable=False)
    grade_level = Column(String, nullable=True)

    # Owner teacher (creator)
    owner_teacher_id = Column(
        UUID(as_uuid=True), ForeignKey("teachers.user_id"), index=True
    )

    # Settings
    is_active = Column(Boolean, default=True)
    allow_student_questions = Column(Boolean, default=True)
    allow_student_discussions = Column(Boolean, default=True)
    require_approval_to_join = Column(Boolean, default=False)
    allow_parent_view = Column(
        Boolean, default=True
    )  # Parents can view if child is enrolled

    # Limits
    max_students = Column(Integer, default=100)

    # Stats
    total_students = Column(Integer, default=0)
    total_teachers = Column(Integer, default=1)
    total_materials = Column(Integer, default=0)
    total_assignments = Column(Integer, default=0)

    # Schedule
    schedule = Column(Text, nullable=True)  # JSON object with class timings

    # Academic period
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Relationships
    owner_teacher = relationship("Teacher", foreign_keys=[owner_teacher_id])
    teachers = relationship("ClassroomTeacher", back_populates="classroom")
    students = relationship("ClassroomStudent", back_populates="classroom")
    materials = relationship("ClassroomMaterial", back_populates="classroom")
    announcements = relationship("Announcement", back_populates="classroom")
    chat_rooms = relationship("ChatRoom", back_populates="classroom")


class ClassroomTeacher(BaseModel):
    """Many-to-many relationship for multiple teachers in classroom"""

    __tablename__ = "classroom_teachers"

    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id"), index=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.user_id"), index=True)

    role = Column(String, default=ClassroomRole.TEACHER)  # owner, teacher, assistant

    # Permissions
    can_add_materials = Column(Boolean, default=True)
    can_create_assignments = Column(Boolean, default=True)
    can_grade_students = Column(Boolean, default=True)
    can_remove_students = Column(Boolean, default=False)

    # Join info
    invited_by = Column(
        UUID(as_uuid=True), ForeignKey("teachers.user_id"), nullable=True
    )

    # Relationships
    classroom = relationship("Classroom", back_populates="teachers")
    teacher = relationship("Teacher", foreign_keys=[teacher_id])

    __table_args__ = (
        UniqueConstraint("classroom_id", "teacher_id", name="uq_classroom_teacher"),
    )
