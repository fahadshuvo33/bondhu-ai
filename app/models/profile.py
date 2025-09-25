from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models._base import BaseModel


class Profile(BaseModel):
    """Common profile information for all user types"""

    __tablename__ = "profiles"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True
    )

    # Personal info
    full_name = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)  # male, female, other, prefer_not_to_say

    # Contact & Location
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    district = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)

    # Preferences
    preferred_language = Column(String, default="en")  # en, bn
    timezone = Column(String, default="Asia/Dhaka")

    # Avatar and Bio
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", backref="profile", uselist=False)
