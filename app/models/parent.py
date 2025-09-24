from sqlalchemy import Column, String, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models._base import BaseModel


class Parent(BaseModel):
    """Parent-specific information"""

    __tablename__ = "parents"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True
    )

    # Parent specific
    occupation = Column(String, nullable=True)
    nid_number = Column(String, nullable=True)  # National ID for verification

    # Notification preferences
    notify_on_child_activity = Column(Boolean, default=True)
    notify_on_low_credits = Column(Boolean, default=True)
    notify_weekly_report = Column(Boolean, default=True)
    notify_on_grade_update = Column(Boolean, default=True)

    # Child monitoring preferences
    monitor_chat_content = Column(Boolean, default=False)
    monitor_study_materials = Column(Boolean, default=True)
    require_approval_for_ai_models = Column(Boolean, default=False)

    # Spending limits
    monthly_credit_limit = Column(Integer, nullable=True)
    require_approval_above_credits = Column(Integer, nullable=True)

    # Dashboard preferences
    dashboard_widgets = Column(Text, nullable=True)  # JSON array of widget preferences

    # Relationships
    user = relationship("User", backref="parent", uselist=False)
    # Children are accessed through User.children (from Student model)
