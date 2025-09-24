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
from app.models.base import BaseModel
from enum import Enum


class ChatRoomType(str, Enum):
    PDF_BASED = "pdf_based"  # Chat based on specific PDF
    SYLLABUS_BASED = "syllabus_based"  # Chat based on syllabus section
    GENERAL = "general"  # Normal chat room
    ANNOUNCEMENT = "announcement"  # One-way announcement room
    HELP = "help"  # Q&A support room


class ChatRoom(BaseModel):
    """Different types of chat rooms in classroom"""

    __tablename__ = "chat_rooms"

    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id"), index=True)

    # Room info
    name = Column(String, nullable=False)
    room_type = Column(String, nullable=False)  # Using ChatRoomType enum
    description = Column(Text, nullable=True)

    # For PDF-based rooms
    study_material_id = Column(
        UUID(as_uuid=True), ForeignKey("study_materials.id"), nullable=True
    )

    # For syllabus-based rooms
    syllabus_section = Column(String, nullable=True)
    syllabus_topics = Column(Text, nullable=True)  # JSON array of topics

    # Settings
    is_active = Column(Boolean, default=True)
    allow_student_messages = Column(Boolean, default=True)
    allow_file_sharing = Column(Boolean, default=False)
    require_teacher_approval = Column(Boolean, default=False)

    # Parent access
    allow_parent_read = Column(Boolean, default=True)

    # AI settings
    ai_assistant_enabled = Column(Boolean, default=True)
    ai_model_preference = Column(String, nullable=True)  # preferred AI model

    # Stats
    total_messages = Column(Integer, default=0)
    total_participants = Column(Integer, default=0)

    # Created by
    created_by_teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.user_id"))

    # Relationships
    classroom = relationship("Classroom", back_populates="chat_rooms")
    study_material = relationship("StudyMaterial")
    messages = relationship("ChatRoomMessage", back_populates="chat_room")
    participants = relationship("ChatRoomParticipant", back_populates="chat_room")


class ChatRoomMessage(BaseModel):
    """Messages in classroom chat rooms"""

    __tablename__ = "chat_room_messages"

    chat_room_id = Column(UUID(as_uuid=True), ForeignKey("chat_rooms.id"), index=True)

    # Sender info
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    sender_type = Column(String)  # student, teacher, ai_assistant

    # Message content
    content = Column(Text, nullable=False)

    # Reply to
    reply_to_message_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_room_messages.id"), nullable=True
    )

    # Attachments
    has_attachment = Column(Boolean, default=False)
    attachment_url = Column(String, nullable=True)
    attachment_type = Column(String, nullable=True)

    # Moderation
    is_approved = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)
    deletion_reason = Column(String, nullable=True)

    # AI-related
    is_ai_generated = Column(Boolean, default=False)
    ai_model_used = Column(String, nullable=True)
    credits_used = Column(Float, nullable=True)

    # Reactions/likes
    likes_count = Column(Integer, default=0)

    # Edit history
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    chat_room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User")
    reply_to = relationship("ChatRoomMessage", remote_side="ChatRoomMessage.id")


class ChatRoomParticipant(BaseModel):
    """Track participants in chat rooms"""

    __tablename__ = "chat_room_participants"

    chat_room_id = Column(UUID(as_uuid=True), ForeignKey("chat_rooms.id"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    # Role in chat
    role = Column(String)  # student, teacher, parent_viewer, moderator

    # Permissions
    can_send_messages = Column(Boolean, default=True)
    can_delete_own_messages = Column(Boolean, default=True)
    can_use_ai = Column(Boolean, default=True)

    # Parent viewing
    is_parent_viewer = Column(Boolean, default=False)
    viewing_child_id = Column(
        UUID(as_uuid=True), nullable=True
    )  # Which child they're viewing for

    # Activity
    last_read_at = Column(DateTime(timezone=True), nullable=True)
    unread_count = Column(Integer, default=0)

    # Mute settings
    is_muted = Column(Boolean, default=False)
    muted_until = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    chat_room = relationship("ChatRoom", back_populates="participants")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("chat_room_id", "user_id", name="uq_chatroom_participant"),
    )
