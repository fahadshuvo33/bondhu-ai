from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    ForeignKey,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models._base import BaseModel


class DocumentMaster(BaseModel):
    """Master document storage - one copy per unique document"""

    __tablename__ = "document_masters"

    # Document identification
    file_hash = Column(String, unique=True, nullable=False, index=True)  # SHA-256 hash
    file_size = Column(Integer, nullable=False)

    # Storage
    storage_path = Column(String, nullable=False)  # S3 or local path
    storage_type = Column(String, default="s3")  # s3, local, gcs

    # Document metadata
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, docx
    mime_type = Column(String, nullable=False)

    # Extracted metadata
    title = Column(String, nullable=True)
    author = Column(String, nullable=True)
    creation_date = Column(DateTime, nullable=True)
    modification_date = Column(DateTime, nullable=True)

    # Content analysis
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    language = Column(String, nullable=True)
    has_images = Column(Boolean, default=False)
    has_tables = Column(Boolean, default=False)
    has_equations = Column(Boolean, default=False)

    # Processing status
    text_extracted = Column(Boolean, default=False)
    ocr_applied = Column(Boolean, default=False)
    embeddings_generated = Column(Boolean, default=False)

    # Vector DB migration fields
    vector_db_indexed = Column(Boolean, default=False)
    vector_db_id = Column(String, nullable=True)  # ID in external vector DB
    vector_db_collection = Column(String, nullable=True)  # Collection/index name

    # Usage tracking
    reference_count = Column(Integer, default=0)  # How many users have this
    total_access_count = Column(Integer, default=0)

    # Relationships
    chunks = relationship(
        "DocumentChunkMaster", back_populates="document", cascade="all, delete-orphan"
    )
    user_documents = relationship("UserDocument", back_populates="master_document")


class DocumentChunkMaster(BaseModel):
    """Master chunk storage with vectors"""

    __tablename__ = "document_chunk_masters"

    document_master_id = Column(
        UUID(as_uuid=True), ForeignKey("document_masters.id"), index=True
    )

    # Chunk identification
    chunk_hash = Column(String, nullable=False, index=True)  # Hash of content
    chunk_index = Column(Integer, nullable=False)

    # Content
    content = Column(Text, nullable=False)
    content_tokens = Column(Integer, nullable=False)  # Token count for LLM context

    # Metadata
    page_number = Column(Integer, nullable=True)
    section_title = Column(String, nullable=True)
    chunk_type = Column(
        String, default="text"
    )  # text, title, table, equation, image_description

    # Hierarchical structure
    parent_chunk_id = Column(
        UUID(as_uuid=True), ForeignKey("document_chunk_masters.id"), nullable=True
    )
    depth_level = Column(Integer, default=0)  # 0=root, 1=chapter, 2=section, etc.

    # Vector embedding
    embedding = Column(Vector(1536), nullable=True)  # Keep for hybrid search
    embedding_model = Column(String, nullable=True)
    embedding_version = Column(String, nullable=True)  # Track model versions

    # Vector DB fields
    vector_db_indexed = Column(Boolean, default=False)
    vector_db_id = Column(String, nullable=True)  # ID in external vector DB
    vector_metadata = Column(Text, nullable=True)  # JSON metadata stored in vector DB

    # Relationships
    document = relationship("DocumentMaster", back_populates="chunks")
    parent = relationship("DocumentChunkMaster", remote_side="DocumentChunkMaster.id")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("document_master_id", "chunk_index", name="uq_document_chunk"),
    )


class UserDocument(BaseModel):
    """User's reference to master documents"""

    __tablename__ = "user_documents"

    # User reference
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("students.user_id"), nullable=True
    )

    # Document reference
    master_document_id = Column(
        UUID(as_uuid=True), ForeignKey("document_masters.id"), index=True
    )

    # User's metadata for the document
    custom_title = Column(String, nullable=True)  # User can rename
    subject = Column(String, nullable=True)
    topic = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array

    # Organization
    folder_id = Column(UUID(as_uuid=True), nullable=True)
    is_favorite = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)

    # Sharing
    is_shared_in_classroom = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    share_token = Column(String, unique=True, nullable=True)

    # User's study progress
    last_page_read = Column(Integer, nullable=True)
    reading_progress_percent = Column(Float, default=0.0)
    total_time_spent_minutes = Column(Integer, default=0)

    # Analytics
    questions_asked = Column(Integer, default=0)
    notes_added = Column(Integer, default=0)
    highlights_added = Column(Integer, default=0)

    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    # Unique constraint - one document per user
    __table_args__ = (
        UniqueConstraint("user_id", "master_document_id", name="uq_user_document"),
    )

    # Relationships
    user = relationship("User")
    student = relationship("Student")
    master_document = relationship("DocumentMaster", back_populates="user_documents")
    chat_sessions = relationship("ChatSession", back_populates="user_document")
    annotations = relationship("DocumentAnnotation", back_populates="user_document")
    study_materials = relationship("StudyMaterial", back_populates="user_document")


class DocumentSimilarity(BaseModel):
    """Track similar documents for recommendations"""

    __tablename__ = "document_similarities"

    document_a_id = Column(
        UUID(as_uuid=True), ForeignKey("document_masters.id"), index=True
    )
    document_b_id = Column(
        UUID(as_uuid=True), ForeignKey("document_masters.id"), index=True
    )

    # Similarity metrics
    content_similarity = Column(Float)  # 0-1 cosine similarity
    structural_similarity = Column(Float, nullable=True)  # Based on outline
    topic_similarity = Column(Float, nullable=True)  # Based on extracted topics

    # Overall similarity
    overall_similarity = Column(Float)  # Weighted average

    # Metadata
    similarity_version = Column(String)  # Algorithm version
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Ensure unique pairs
    __table_args__ = (
        UniqueConstraint("document_a_id", "document_b_id", name="uq_document_pair"),
    )


class VectorDBSync(BaseModel):
    """Track vector database synchronization"""

    __tablename__ = "vector_db_sync"

    # Entity being synced
    entity_type = Column(String)  # document_master, document_chunk
    entity_id = Column(UUID(as_uuid=True), index=True)

    # Sync status
    sync_status = Column(String)  # pending, syncing, completed, failed
    sync_action = Column(String)  # insert, update, delete

    # Vector DB details
    vector_db_name = Column(String)  # pinecone, weaviate, qdrant
    collection_name = Column(String)
    vector_id = Column(String, nullable=True)

    # Sync metadata
    last_sync_attempt = Column(DateTime(timezone=True))
    sync_completed_at = Column(DateTime(timezone=True), nullable=True)
    sync_error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint(
            "entity_type", "entity_id", "vector_db_name", name="uq_vector_sync"
        ),
    )
