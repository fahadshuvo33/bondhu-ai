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
from app.models._base import BaseModel
from enum import Enum
from sqlalchemy import Index, UniqueConstraint


class CreditType(str, Enum):
    FREE_DAILY = "free_daily"  # Daily login bonus (30 days validity)
    FREE_ACTIVITY = "free_activity"  # Activity rewards (30 days validity)
    SUBSCRIPTION_BONUS = "subscription_bonus"  # Plan bonus (custom validity)
    PAID = "paid"  # Purchased credits (no expiry)
    PROMOTIONAL = "promotional"  # Special promos (custom validity)
    REFERRAL = "referral"  # Referral bonus (custom validity)


class TransactionType(str, Enum):
    PURCHASE = "purchase"
    SPEND = "spend"
    BONUS = "bonus"
    REFUND = "refund"
    EXPIRED = "expired"
    TRANSFER = "transfer"
    CLASSROOM_ALLOCATION = "classroom_allocation"


class Credit(BaseModel):
    """User credit balance and settings"""

    __tablename__ = "credits"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True
    )

    # Total available balance (sum of all non-expired credits)
    balance = Column(Float, default=0.0)

    # Breakdown by type
    free_credits = Column(Float, default=0.0)  # Expiring credits
    paid_credits = Column(Float, default=0.0)  # Non-expiring credits

    # Lifetime totals
    total_earned_free = Column(Float, default=0.0)
    total_purchased = Column(Float, default=0.0)
    total_spent = Column(Float, default=0.0)
    total_expired = Column(Float, default=0.0)

    # Daily bonus tracking
    last_daily_bonus_at = Column(DateTime(timezone=True), nullable=True)
    daily_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)

    # Limits (for parental control)
    daily_spend_limit = Column(Float, nullable=True)
    monthly_spend_limit = Column(Float, nullable=True)

    # Usage tracking
    spent_today = Column(Float, default=0.0)
    spent_this_month = Column(Float, default=0.0)
    last_reset_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="credits")
    ledger_entries = relationship(
        "CreditLedger",
        back_populates="credit_account",
        order_by="desc(CreditLedger.created_at)",
    )


class CreditLedger(BaseModel):
    """Individual credit entries with expiration tracking"""

    __tablename__ = "credit_ledger"

    credit_id = Column(UUID(as_uuid=True), ForeignKey("credits.id"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    # Credit details
    credit_type = Column(String)  # Using CreditType enum
    amount = Column(Float)

    # Balance tracking
    balance_remaining = Column(Float)  # Current remaining from this entry
    is_depleted = Column(Boolean, default=False)  # Fully used up

    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)  # NULL = never expires
    is_expired = Column(Boolean, default=False)
    expired_amount = Column(Float, default=0.0)  # How much expired unused

    # Source information
    source = Column(String)  # daily_login, activity, purchase, subscription, etc.
    source_reference = Column(
        String, nullable=True
    )  # Transaction ID, activity name, etc.
    description = Column(String)

    # Metadata (rename attribute to avoid SQLAlchemy reserved name 'metadata')
    meta_json = Column("metadata", Text, nullable=True)  # JSON for additional info

    # Relationships
    credit_account = relationship("Credit", back_populates="ledger_entries")
    user = relationship("User")
    usage_records = relationship("CreditUsage", back_populates="ledger_entry")

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_credit_ledger_expiry", "expires_at", "is_expired"),
        Index(
            "idx_credit_ledger_balance", "user_id", "balance_remaining", "is_depleted"
        ),
    )


class CreditUsage(BaseModel):
    """Track which credits were used for what"""

    __tablename__ = "credit_usage"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("credit_ledger.id"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    # Usage details
    amount_used = Column(Float)
    used_for = Column(String)  # ai_chat, pdf_analysis, image_generation, etc.

    # Reference to what consumed the credits
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    reference_type = Column(String, nullable=True)  # chat_message, ai_request, etc.

    # Context
    classroom_id = Column(UUID(as_uuid=True), nullable=True)
    chat_room_id = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    ledger_entry = relationship("CreditLedger", back_populates="usage_records")
    user = relationship("User")


class CreditTransaction(BaseModel):
    """High-level credit transactions (for user history)"""

    __tablename__ = "credit_transactions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    transaction_type = Column(String)
    amount = Column(Float)
    balance_before = Column(Float)
    balance_after = Column(Float)

    description = Column(String)

    # Related ledger entries (can be multiple for expiration)
    ledger_entries = Column(Text, nullable=True)  # JSON array of ledger IDs

    # Payment reference (if purchase)
    payment_id = Column(UUID(as_uuid=True), nullable=True)

    # Transfer details
    transfer_to_user_id = Column(UUID(as_uuid=True), nullable=True)
    transfer_from_user_id = Column(UUID(as_uuid=True), nullable=True)

    # Classroom allocation
    classroom_id = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    user = relationship("User")


class DailyBonus(BaseModel):
    """Track daily bonus history"""

    __tablename__ = "daily_bonuses"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    # Bonus details
    amount = Column(Float)
    streak_day = Column(Integer)

    # Bonus multipliers
    base_amount = Column(Float)
    streak_multiplier = Column(Float, default=1.0)
    special_multiplier = Column(Float, default=1.0)  # Weekend, holiday bonuses

    # Ledger reference
    ledger_id = Column(UUID(as_uuid=True), ForeignKey("credit_ledger.id"))

    # Date (to prevent multiple claims)
    bonus_date = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint - one bonus per user per day
    __table_args__ = (UniqueConstraint("user_id", "bonus_date", name="uq_daily_bonus"),)

    # Relationships
    user = relationship("User")
    ledger_entry = relationship("CreditLedger")


class SubscriptionCredit(BaseModel):
    """Track subscription-based credit allocations"""

    __tablename__ = "subscription_credits"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    subscription_id = Column(
        UUID(as_uuid=True), index=True
    )  # Reference to subscription

    # Credit allocation
    credits_amount = Column(Float)
    validity_days = Column(Integer)  # Custom validity period

    # Ledger reference
    ledger_id = Column(UUID(as_uuid=True), ForeignKey("credit_ledger.id"))

    # Plan details
    plan_name = Column(String)
    plan_tier = Column(String)  # basic, pro, premium

    # Relationships
    user = relationship("User")
    ledger_entry = relationship("CreditLedger")


class ClassroomCreditPool(BaseModel):
    """Credit pool for classroom use"""

    __tablename__ = "classroom_credit_pools"

    classroom_id = Column(
        UUID(as_uuid=True), ForeignKey("classrooms.id"), unique=True, index=True
    )

    # Pool balance
    balance = Column(Float, default=0.0)
    total_allocated = Column(Float, default=0.0)
    total_used = Column(Float, default=0.0)

    # Limits
    daily_limit = Column(Float, nullable=True)
    per_student_daily_limit = Column(Float, nullable=True)
    per_student_monthly_limit = Column(Float, nullable=True)

    # Settings
    allow_student_use = Column(Boolean, default=True)
    require_approval_above = Column(Float, nullable=True)

    # Usage tracking
    used_today = Column(Float, default=0.0)
    used_this_month = Column(Float, default=0.0)
    last_reset_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    classroom = relationship("Classroom", backref="credit_pool")
