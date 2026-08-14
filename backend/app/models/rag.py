import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Boolean, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base

# Safe import fallback for pgvector to ensure local execution runs without crash
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy.types import UserDefinedType
    class Vector(UserDefinedType):
        def __init__(self, dim):
            self.dim = dim
        def get_col_spec(self, **kw):
            return f"vector({self.dim})"


class LessonChunkEmbedding(Base):
    __tablename__ = "lesson_chunk_embedding"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(UUID(as_uuid=True), ForeignKey("section.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lesson.id", ondelete="CASCADE"), nullable=False, index=True)
    
    content_chunk = Column(Text, nullable=False)
    chunk_type = Column(String(50), nullable=False, default="notes") # 'notes', 'pdf', 'transcript'
    start_timestamp_seconds = Column(Integer, nullable=True)
    end_timestamp_seconds = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)
    
    # 384 dimensions matching sentence-transformers 'all-MiniLM-L6-v2'
    embedding = Column(Vector(384), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    course = relationship("Course")
    section = relationship("Section")
    lesson = relationship("Lesson")


class AITutorConversation(Base):
    __tablename__ = "ai_tutor_conversation"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.user_id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lesson.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(255), nullable=False, default="AI Tutor Chat")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    student = relationship("Student")
    course = relationship("Course")
    lesson = relationship("Lesson")
    messages = relationship("AITutorMessage", back_populates="conversation", cascade="all, delete-orphan")


class AITutorMessage(Base):
    __tablename__ = "ai_tutor_message"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_tutor_conversation.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(50), nullable=False) # 'user' or 'ai'
    content = Column(Text, nullable=False)
    
    # JSON list of citation objects [{lesson_id, lesson_title, chunk_type, timestamp_seconds, snippet}]
    citations = Column(JSON().with_variant(JSONB(astext_type=Text()), "postgresql"), nullable=True)
    confidence_score = Column(Float, nullable=False, default=1.0)
    was_escalated = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("AITutorConversation", back_populates="messages")
