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
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models._base import BaseModel


class StudyMaterial(BaseModel):
    """PDFs and other study materials uploaded by students"""

    __tablename__ = "study_materials"

    # Owner information
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.user_id"), index=True)
    uploaded_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    # File info
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, docx, pptx
    file_size = Column(Integer, nullable=False)  # in bytes
    file_url = Column(String, nullable=False)
    file_hash = Column(String, nullable=True)  # For duplicate detection

    # Material metadata
    title = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    topic = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    language = Column(String, default="en")  # en, bn, mixed

    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_status = Column(
        String, default="pending"
    )  # pending, processing, completed, failed
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)

    # Extracted content
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    has_images = Column(Boolean, default=False)
    has_tables = Column(Boolean, default=False)

    # Vector search
    embeddings_generated = Column(Boolean, default=False)
    embedding_model = Column(String, nullable=True)  # text-embedding-ada-002, etc.
    total_chunks = Column(Integer, default=0)

    # AI-generated metadata
    ai_summary = Column(Text, nullable=True)
    ai_key_topics = Column(Text, nullable=True)  # JSON array
    ai_difficulty_level = Column(
        String, nullable=True
    )  # beginner, intermediate, advanced
    ai_prerequisites = Column(Text, nullable=True)  # JSON array

    # Usage stats
    view_count = Column(Integer, default=0)
    questions_asked = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    # Sharing settings
    is_shared_in_classroom = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)

    # Relationships
    student = relationship("Student", back_populates="study_materials")
    uploader = relationship("User")
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )
    chat_sessions = relationship("ChatSession", back_populates="study_material")
    classrooms = relationship("ClassroomMaterial", back_populates="study_material")


class DocumentChunk(BaseModel):
    """Vector embeddings for document chunks"""

    __tablename__ = "document_chunks"

    document_id = Column(
        UUID(as_uuid=True), ForeignKey("study_materials.id"), index=True
    )

    # Chunk information
    chunk_index = Column(Integer, nullable=False)  # Order in document
    page_number = Column(Integer, nullable=True)  # Source page

    # Content
    content = Column(Text, nullable=False)  # Original text
    content_length = Column(Integer, nullable=False)

    # Chunk metadata
    chunk_type = Column(String, default="text")  # text, title, table, list, code
    section_title = Column(String, nullable=True)  # Detected section/chapter

    # Vector embedding (1536 dimensions for OpenAI, adjust based on model)
    embedding = Column(Vector(1536), nullable=True)

    # Processing metadata
    embedding_model = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Search optimization
    keywords = Column(Text, nullable=True)  # JSON array of important terms

    # Relationships
    document = relationship("StudyMaterial", back_populates="chunks")

    # Indexes for vector similarity search
    __table_args__ = (
        Index(
            "idx_document_chunks_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class SearchQuery(BaseModel):
    """Track search queries for analytics and caching"""

    __tablename__ = "search_queries"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    study_material_id = Column(
        UUID(as_uuid=True), ForeignKey("study_materials.id"), nullable=True
    )

    # Query details
    query_text = Column(Text, nullable=False)
    query_type = Column(String)  # semantic, keyword, hybrid

    # Query embedding for similarity matching
    query_embedding = Column(Vector(1536), nullable=True)

    # Results
    results_count = Column(Integer, default=0)
    top_chunk_ids = Column(Text, nullable=True)  # JSON array

    # Performance metrics
    search_time_ms = Column(Integer, nullable=True)

    # User feedback
    was_helpful = Column(Boolean, nullable=True)

    # Context
    chat_session_id = Column(UUID(as_uuid=True), nullable=True)
    classroom_id = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    user = relationship("User")
    study_material = relationship("StudyMaterial")
