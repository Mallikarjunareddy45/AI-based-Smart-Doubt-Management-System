import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base_class import Base

# Dialect variant type mapping: JSONB on Postgres, standard JSON on SQLite
JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")

class ActivityLog(Base):
    __tablename__ = "activity_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True) # e.g. "ask_question", "assign_tutor", "manual_override"
    entity_type = Column(String(50), nullable=True) # e.g. "question", "cluster", "user"
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    # Using JSONB for advanced PostgreSQL JSON query performance
    payload = Column(JSON_TYPE, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User")


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshot"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"), nullable=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True) # e.g. "average_wait_time", "resolution_rate"
    metric_value = Column(Float, nullable=False)
    snapshot_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    course = relationship("Course")


class Report(Base):
    __tablename__ = "report"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    report_type = Column(String(50), nullable=False) # e.g. "tutor_performance", "course_health"
    data = Column(JSON_TYPE, nullable=False) # Structured data payload
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User")
