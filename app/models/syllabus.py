from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models._base import BaseModel
from enum import Enum


class SyllabusStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Syllabus(BaseModel):
    """Model for syllabuses created by students from study materials."""

    __tablename__ = "syllabuses"

    student_id = Column(
        UUID(as_uuid=True), ForeignKey("students.user_id"), index=True
    )
    study_material_id = Column(
        UUID(as_uuid=True), ForeignKey("study_materials.id"), index=True
    )

    # Syllabus info
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default=SyllabusStatus.DRAFT)
    version = Column(Integer, default=1)

    # Structure (e.g., chapters, topics, page ranges)
    structure = Column(Text, nullable=False)  # JSON array of sections/topics

    # AI-generated content
    ai_overview = Column(Text, nullable=True)
    ai_learning_objectives = Column(Text, nullable=True)  # JSON array

    # Usage tracking
    chat_room_count = Column(Integer, default=0)
    quiz_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    student = relationship("Student", backref="syllabuses")
    study_material = relationship("StudyMaterial", backref="syllabuses")
    syllabus_chat_rooms = relationship("SyllabusChatRoom", back_populates="syllabus")


class SyllabusChatRoom(BaseModel):
    """Chat rooms specifically linked to a syllabus section/topic."""

    __tablename__ = "syllabus_chat_rooms"

    syllabus_id = Column(UUID(as_uuid=True), ForeignKey("syllabuses.id"), index=True)
    chat_room_id = Column(UUID(as_uuid=True), ForeignKey("chat_rooms.id"), index=True)
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("students.user_id"), index=True
    )

    # Context of this specific chat room
    section_title = Column(String, nullable=True)
    topic_title = Column(String, nullable=True)
    page_range = Column(String, nullable=True)  # e.g., "10-25"

    # AI settings specific to this chat room
    ai_mode = Column(String, default="rag_qa")  # rag_qa, quiz_mode, mock_exam_mode
    ai_difficulty = Column(String, nullable=True)

    # Stats
    total_messages = Column(Integer, default=0)
    total_quizzes_generated = Column(Integer, default=0)
    total_mock_exams_generated = Column(Integer, default=0)

    # Relationships
    syllabus = relationship("Syllabus", back_populates="syllabus_chat_rooms")
    chat_room = relationship("ChatRoom", backref="syllabus_link", uselist=False)
    student = relationship("Student")
