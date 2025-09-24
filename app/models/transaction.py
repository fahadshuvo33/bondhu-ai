from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PaymentProvider(str, enum.Enum):
    BKASH = "bkash"
    NAGAD = "nagad"
    CARD = "card"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    transaction_id = Column(String, unique=True, index=True)
    provider = Column(Enum(PaymentProvider))

    amount = Column(Float)
    credits_purchased = Column(Float)

    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    provider_reference = Column(String, nullable=True)
    provider_response = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="transactions")
