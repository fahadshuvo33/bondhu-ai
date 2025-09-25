from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime
from app.models._base import BaseModelWithIntID


class CreditConfig(BaseModelWithIntID):
    """System-wide credit configuration (DEPRECATED: Use SystemConfig instead)"""

    __tablename__ = "credit_config"

    # Daily bonus settings
    daily_bonus_enabled = Column(Boolean, default=True)
    daily_bonus_base_amount = Column(Float, default=1.0)
    daily_bonus_validity_days = Column(Integer, default=30)

    # Streak bonuses
    streak_bonus_enabled = Column(Boolean, default=True)
    streak_multipliers = Column(Text)  # JSON: {7: 1.5, 14: 2.0, 30: 3.0}

    # Activity bonuses
    activity_bonus_validity_days = Column(Integer, default=30)
    activity_bonuses = Column(
        Text
    )  # JSON: {"first_pdf_upload": 5, "complete_profile": 3}

    # Credit costs
    ai_chat_cost = Column(Text)  # JSON: {"gpt-4": 2.0, "claude": 2.5, "gemini": 1.5}
    pdf_analysis_cost_per_page = Column(Float, default=0.1)
    image_generation_cost = Column(Float, default=5.0)

    # Expiration settings
    expiration_check_interval_hours = Column(Integer, default=6)
    notify_before_expiry_days = Column(Integer, default=3)

    # Purchase bonuses
    purchase_bonuses = Column(Text)  # JSON: {"100": 10, "500": 75, "1000": 200}

    # Referral settings
    referral_bonus_amount = Column(Float, default=10.0)
    referral_bonus_validity_days = Column(Integer, default=60)
    referrer_bonus_amount = Column(Float, default=5.0)

    # Is this the active configuration?
    is_active = Column(Boolean, default=True)

    # Deprecation fields
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    replaced_by_config_name = Column(String, nullable=True)
