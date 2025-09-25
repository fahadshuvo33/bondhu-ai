# pdf_library.py
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.models._base import BaseModel


class PDFLibrary(BaseModel):
    """Admin-managed PDF library that users can directly use"""
    
    __tablename__ = "pdf_library"
    
    # Basic info
    title = Column(String, nullable=False, index=True)
    author = Column(String, nullable=True)
    publisher = Column(String, nullable=True)
    isbn = Column(String, nullable=True, unique=True)
    
    # Categorization
    subject = Column(String, nullable=False, index=True)  # Math, Science, English
    category = Column(String, nullable=True)  # Textbook, Reference, Practice
    sub_category = Column(String, nullable=True)  # Algebra, Geometry, etc.
    
    # Educational level
    education_level = Column(String, nullable=True)  # primary, secondary, higher_secondary
    grade_levels = Column(ARRAY(Integer), nullable=True)  # [6, 7, 8] for multi-grade
    curriculum = Column(String, nullable=True)  # Bangladesh, Cambridge, etc.
    
    # File info
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)  # in bytes
    page_count = Column(Integer, nullable=True)
    language = Column(String, default="en")
    
    # Metadata
    description = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    thumbnail_url = Column(String, nullable=True)
    preview_url = Column(String, nullable=True)  # first few pages preview
    
    # Availability
    is_active = Column(Boolean, default=True)
    is_free = Column(Boolean, default=True)
    required_subscription = Column(String, nullable=True)  # pro, premium
    
    # Usage stats
    total_users = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    avg_rating = Column(Integer, nullable=True)
    
    # Admin management
    uploaded_by_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_by_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    chunk_count = Column(Integer, default=0)
    
    # Relationships
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_admin_id])
    approved_by = relationship("User", foreign_keys=[approved_by_admin_id])
    user_accesses = relationship("UserLibraryAccess", back_populates="library_pdf")


class UserLibraryAccess(BaseModel):
    """Track which users have accessed which library PDFs"""
    
    __tablename__ = "user_library_accesses"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    library_pdf_id = Column(UUID(as_uuid=True), ForeignKey("pdf_library.id"), index=True)
    
    # Access info
    first_accessed_at = Column(DateTime(timezone=True), nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=False)
    access_count = Column(Integer, default=1)
    
    # User preferences
    is_favorite = Column(Boolean, default=False)
    user_rating = Column(Integer, nullable=True)  # 1-5
    last_page_read = Column(Integer, default=0)
    reading_progress = Column(Integer, default=0)  # percentage
    
    # Study info
    total_study_time = Column(Integer, default=0)  # in seconds
    notes_count = Column(Integer, default=0)
    highlights_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User")
    library_pdf = relationship("PDFLibrary", back_populates="user_accesses")