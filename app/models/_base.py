import uuid
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
from app.core.database import Base


class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps"""

    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )

    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), onupdate=func.now())


class UUIDMixin:
    """Mixin for adding UUID primary key"""

    @declared_attr
    def id(cls):
        return Column(
            UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
        )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """Base model with UUID and timestamps"""

    __abstract__ = True


class BaseModelWithIntID(Base, TimestampMixin):
    """Base model with Integer ID and timestamps (for legacy or specific needs)"""

    __abstract__ = True

    @declared_attr
    def id(cls):
        return Column(Integer, primary_key=True, index=True)
