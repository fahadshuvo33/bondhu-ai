from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class AIProvider(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MIXTRAL = "mixtral"


class RequestType(str, enum.Enum):
    CHAT = "chat"
    IMAGE_ANALYSIS = "image_analysis"
    PDF_ANALYSIS = "pdf_analysis"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"


class AIRequest(Base):
    __tablename__ = "ai_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    request_type = Column(Enum(RequestType))
    provider = Column(Enum(AIProvider))
    model = Column(String)  # gpt-4, claude-3, gemini-pro, etc

    prompt = Column(Text)
    response = Column(Text, nullable=True)

    credits_charged = Column(Float)
    actual_cost = Column(Float, nullable=True)  # Track actual API cost

    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)

    file_url = Column(String, nullable=True)  # For image/pdf uploads

    status = Column(String, default="pending")  # pending, completed, failed
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="ai_requests")
