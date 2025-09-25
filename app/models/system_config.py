from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.models._base import BaseModelWithIntID, BaseModel
from enum import Enum


class SystemConfigType(str, Enum):
    AI_CONFIG = "ai_config"
    CREDIT_CONFIG = "credit_config"
    FEATURE_FLAGS = "feature_flags"
    GENERAL_SETTINGS = "general_settings"
    EMAIL_TEMPLATES = "email_templates"
    NOTIFICATION_SETTINGS = "notification_settings"


class SystemConfig(BaseModel):
    """System-wide configuration settings."""

    __tablename__ = "system_configs"

    config_name = Column(String, unique=True, nullable=False, index=True)
    config_type = Column(String, default=SystemConfigType.GENERAL_SETTINGS)
    config_value = Column(Text, nullable=False)  # Stored as JSON string
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_updated_by_admin_id = Column(UUID(as_uuid=True), nullable=True)
    last_updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
