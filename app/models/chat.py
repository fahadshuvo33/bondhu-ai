from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    ForeignKey,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from enum import Enum


class ChatContextType(str, Enum):
    PDF_BASED = "pdf_based"
    SYLLABUS_BASED = "syllabus_based"
    GENERAL = "general"
    QUIZ = "quiz"
    HOMEWORK_HELP = "homework_help"


class ChatSession(BaseModel):
    """Chat sessions for study materials"""

    __tablename__ = "chat_sessions"

    # Owner
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.user_id"), index=True)

    # Context
    context_type = Column(String, default=ChatContextType.PDF_BASED)
    study_material_id = Column(
        UUID(as_uuid=True), ForeignKey("study_materials.id"), nullable=True, index=True
    )
    classroom_id = Column(
        UUID(as_uuid=True), ForeignKey("classrooms.id"), nullable=True
    )

    # Session info
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # AI settings
    preferred_model = Column(String, nullable=True)  # gpt-4, claude, etc.
    temperature = Column(Float, default=0.7)
    system_prompt = Column(Text, nullable=True)

    # Context window management
    max_context_messages = Column(Integer, default=20)
    summarize_after_messages = Column(Integer, default=50)

    # Status
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)

    # Stats
    message_count = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_credits_used = Column(Float, default=0.0)

    # Vector search context (for PDF-based)
    relevant_chunk_ids = Column(Text, nullable=True)  # JSON array of chunk IDs
    search_scope = Column(String, default="full")  # full, chapter, page_range

    # Timestamps
    last_message_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="chat_sessions")
    study_material = relationship("StudyMaterial", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )
    summaries = relationship("ChatSummary", back_populates="session")

    user_document_id = Column(
        UUID(as_uuid=True), ForeignKey("user_documents.id"), nullable=True, index=True
    )

    # Vector search configuration
    use_vector_db = Column(Boolean, default=False)  # Use external vector DB
    vector_search_params = Column(Text, nullable=True)  # JSON search parameters

    # ... rest of model ...

    # Relationships
    user_document = relationship("UserDocument", back_populates="chat_sessions")


class ChatMessage(BaseModel):
    """Individual messages in a chat session"""

    __tablename__ = "chat_messages"

    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), index=True)

    # Message content
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Vector search context (for this specific message)
    retrieved_chunks = Column(Text, nullable=True)  # JSON array of chunks used
    chunk_relevance_scores = Column(Text, nullable=True)  # JSON array of scores

    # AI details
    model_used = Column(String, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    credits_charged = Column(Float, nullable=True)

    # Response metadata
    response_time_ms = Column(Integer, nullable=True)

    # Citations (from PDF chunks)
    has_citations = Column(Boolean, default=False)
    citations = Column(Text, nullable=True)  # JSON array with page numbers

    # Feedback
    is_helpful = Column(Boolean, nullable=True)
    feedback_text = Column(Text, nullable=True)

    # Attachments
    has_attachment = Column(Boolean, default=False)
    attachment_type = Column(String, nullable=True)  # image, diagram
    attachment_url = Column(String, nullable=True)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class ChatSummary(BaseModel):
    """Periodic summaries of chat sessions to manage context"""

    __tablename__ = "chat_summaries"

    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), index=True)

    # Summary range
    from_message_index = Column(Integer, nullable=False)
    to_message_index = Column(Integer, nullable=False)

    # Summary content
    summary_text = Column(Text, nullable=False)
    key_points = Column(Text, nullable=True)  # JSON array

    # AI details
    model_used = Column(String, nullable=True)
    tokens_used = Column(Integer, nullable=True)

    # Relationships
    session = relationship("ChatSession", back_populates="summaries")
