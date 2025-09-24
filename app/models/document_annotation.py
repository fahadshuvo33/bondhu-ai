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


class AnnotationType(str, Enum):
    HIGHLIGHT = "highlight"
    NOTE = "note"
    BOOKMARK = "bookmark"
    QUESTION = "question"
    SUMMARY = "summary"


class DocumentAnnotation(BaseModel):
    """User annotations on documents"""

    __tablename__ = "document_annotations"

    user_document_id = Column(
        UUID(as_uuid=True), ForeignKey("user_documents.id"), index=True
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    # Annotation type
    annotation_type = Column(String)  # Using AnnotationType enum

    # Location in document
    page_number = Column(Integer, nullable=True)
    chunk_id = Column(
        UUID(as_uuid=True), ForeignKey("document_chunk_masters.id"), nullable=True
    )

    # Position (for highlights)
    start_position = Column(Integer, nullable=True)
    end_position = Column(Integer, nullable=True)
    selected_text = Column(Text, nullable=True)

    # Content
    content = Column(Text, nullable=True)  # Note text, question, etc.
    color = Column(String, nullable=True)  # For highlights

    # AI-generated
    is_ai_generated = Column(Boolean, default=False)
    ai_context = Column(Text, nullable=True)  # What prompted AI annotation

    # Sharing
    is_private = Column(Boolean, default=True)
    shared_in_classroom = Column(Boolean, default=False)

    # Relationships
    user_document = relationship("UserDocument", back_populates="annotations")
    user = relationship("User")
    chunk = relationship("DocumentChunkMaster")
