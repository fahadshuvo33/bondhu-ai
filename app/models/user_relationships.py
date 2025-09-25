# user_relationships.py
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models._base import BaseModel
from datetime import datetime, timezone


class ParentStudentLink(BaseModel):
    """Many-to-many relationship between parents and students"""
    
    __tablename__ = "parent_student_links"
    __table_args__ = (
        UniqueConstraint('parent_id', 'student_id', name='_parent_student_uc'),
    )
    
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    
    # Relationship info
    relationship_type = Column(String, nullable=False)  # mother, father, guardian, other
    is_primary_guardian = Column(Boolean, default=False)
    
    # Permissions - what can parent do
    can_view_progress = Column(Boolean, default=True)
    can_view_chat_history = Column(Boolean, default=False)
    can_manage_subscription = Column(Boolean, default=False)
    can_set_study_restrictions = Column(Boolean, default=False)
    can_approve_purchases = Column(Boolean, default=False)
    
    # Notification settings
    notify_on_login = Column(Boolean, default=False)
    notify_on_quiz_complete = Column(Boolean, default=True)
    notify_on_low_performance = Column(Boolean, default=True)
    notify_daily_summary = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    invitation_status = Column(String, default="pending")  # pending, accepted, rejected
    invitation_code = Column(String, nullable=True, unique=True)
    invited_at = Column(DateTime(timezone=True))
    accepted_at = Column(DateTime(timezone=True))
    rejected_at = Column(DateTime(timezone=True))
    
    # Relationships
    parent = relationship("User", foreign_keys=[parent_id], backref="student_links")
    student = relationship("User", foreign_keys=[student_id], backref="parent_links")


class TeacherStudentLink(BaseModel):
    """Direct teacher-student relationships outside of classroom"""
    
    __tablename__ = "teacher_student_links"
    __table_args__ = (
        UniqueConstraint('teacher_id', 'student_id', 'link_type', name='_teacher_student_type_uc'),
    )
    
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    
    # Link type
    link_type = Column(String, nullable=False)  # private_tutoring, mentorship, consultation, office_hours
    subject = Column(String, nullable=True)  # specific subject for tutoring
    grade_level = Column(String, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    status = Column(String, default="active")  # active, paused, completed, terminated
    
    # Tutoring details (for paid consultations)
    is_paid = Column(Boolean, default=False)
    hourly_rate_credits = Column(Integer, nullable=True)
    total_hours_completed = Column(Integer, default=0)
    total_credits_earned = Column(Integer, default=0)
    
    # Schedule
    meeting_schedule = Column(Text, nullable=True)  # JSON: recurring schedule
    preferred_meeting_platform = Column(String, nullable=True)  # zoom, google_meet, in_app
    next_meeting_at = Column(DateTime(timezone=True))
    last_meeting_at = Column(DateTime(timezone=True))
    
    # Progress tracking
    initial_assessment = Column(Text, nullable=True)  # Teacher's initial assessment
    learning_goals = Column(Text, nullable=True)  # JSON: learning goals
    progress_notes = Column(Text, nullable=True)  # JSON: array of progress notes with dates
    current_level = Column(String, nullable=True)  # beginner, intermediate, advanced
    
    # Timestamps
    requested_at = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    paused_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    
    # Reason for ending (if applicable)
    termination_reason = Column(String, nullable=True)
    terminated_by = Column(String, nullable=True)  # teacher, student, admin
    
    # Relationships
    teacher = relationship("User", foreign_keys=[teacher_id], backref="student_consultations")
    student = relationship("User", foreign_keys=[student_id], backref="teacher_consultations")


class StudentStudentLink(BaseModel):
    """Student-to-student relationships for study groups or peer learning"""
    
    __tablename__ = "student_student_links"
    __table_args__ = (
        UniqueConstraint('student1_id', 'student2_id', name='_student_student_uc'),
    )
    
    student1_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    student2_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    
    # Link type
    link_type = Column(String, nullable=False)  # study_buddy, peer_tutor, group_member
    
    # Status
    is_active = Column(Boolean, default=True)
    invitation_status = Column(String, default="pending")  # pending, accepted, rejected, blocked
    
    # Study preferences
    study_subjects = Column(Text, nullable=True)  # JSON array of common subjects
    study_schedule = Column(Text, nullable=True)  # JSON: preferred study times
    
    # Interaction stats
    total_study_sessions = Column(Integer, default=0)
    total_study_hours = Column(Integer, default=0)
    last_interaction_at = Column(DateTime(timezone=True))
    
    # Timestamps
    requested_at = Column(DateTime(timezone=True))
    accepted_at = Column(DateTime(timezone=True))
    blocked_at = Column(DateTime(timezone=True))
    
    # Relationships
    student1 = relationship("User", foreign_keys=[student1_id], backref="peer_connections_sent")
    student2 = relationship("User", foreign_keys=[student2_id], backref="peer_connections_received")


# Add to the file above

class UserRelationshipMixin:
    """Mixin for common relationship methods"""
    
    @classmethod
    def get_active_relationships(cls, user_id: UUID, db):
        """Get all active relationships for a user"""
        return db.query(cls).filter(
            (cls.is_active == True) & 
            ((cls.parent_id == user_id) | (cls.student_id == user_id))
        ).all()
    
    def accept_invitation(self):
        """Accept a pending invitation"""
        self.invitation_status = "accepted"
        self.accepted_at = datetime.now(timezone.utc)
        self.is_active = True
    
    def reject_invitation(self):
        """Reject a pending invitation"""
        self.invitation_status = "rejected"
        self.rejected_at = datetime.now(timezone.utc)
        self.is_active = False