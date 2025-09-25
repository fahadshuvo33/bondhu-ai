from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models._base import BaseModel
from enum import Enum


class SubscriptionPlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium" # For parents with advanced analytics


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"
    TRIAL = "trial"


class Subscription(BaseModel):
    """Manages user subscriptions and their associated benefits."""

    __tablename__ = "subscriptions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    # Plan details
    plan_type = Column(String, default=SubscriptionPlanType.FREE)
    plan_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, default=0.0)  # For paid plans
    currency = Column(String, default="USD")

    # Status & Dates
    status = Column(String, default=SubscriptionStatus.TRIAL)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)  # Null for free, active for paid
    cancellation_date = Column(DateTime(timezone=True), nullable=True)
    is_auto_renew = Column(Boolean, default=False)

    # Payment info
    payment_method_id = Column(String, nullable=True)  # Stripe payment method ID
    external_subscription_id = Column(String, nullable=True)  # Stripe subscription ID

    # Feature entitlements
    pdf_upload_limit = Column(Integer, default=1)  # Free: 1, Pro: 10, etc.
    syllabus_creation_enabled = Column(Boolean, default=False)
    mock_exam_enabled = Column(Boolean, default=False)
    advanced_analytics_enabled = Column(Boolean, default=False)
    ai_recommendations_enabled = Column(Boolean, default=False)
    classroom_management_enabled = Column(Boolean, default=False)
    lesson_plan_generator_enabled = Column(Boolean, default=False)

    # Credit details (can be separate or linked)
    allocated_credits = Column(Float, default=0.0)  # Credits given with subscription
    credit_validity_days = Column(Integer, nullable=True)  # Days credits are valid

    # Relationships
    user = relationship("User", backref="subscriptions")


class SubscriptionHistory(BaseModel):
    """Records changes in user subscriptions."""

    __tablename__ = "subscription_history"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), index=True)

    # History details
    event_type = Column(String, nullable=False)  # activated, cancelled, upgraded, downgraded, renewed
    old_plan_type = Column(String, nullable=True)
    new_plan_type = Column(String, nullable=False)
    event_date = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User")
    subscription = relationship("Subscription")
