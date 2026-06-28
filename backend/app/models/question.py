import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
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

class QuestionCluster(Base):
    __tablename__ = "question_cluster"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_tutor_id = Column(UUID(as_uuid=True), ForeignKey("tutor.user_id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), default="pending", nullable=False, index=True) # pending, assigned, resolved
    priority_score = Column(Float, default=0.0, nullable=False, index=True)
    summary = Column(String(2000), nullable=True) # AI-generated summary of clustered questions
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    course = relationship("Course", back_populates="clusters")
    assigned_tutor = relationship("Tutor", back_populates="assigned_clusters")
    questions = relationship("Question", back_populates="cluster")
    assignments = relationship("TutorAssignment", back_populates="cluster", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="cluster", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "question"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.user_id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("question_cluster.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(String(10000), nullable=False) # Markdown content support
    status = Column(String(50), default="pending", nullable=False, index=True) # pending, clustered, resolved
    urgency_score = Column(Float, default=0.0, nullable=False) # raw dynamic urgency (wait time + keyword matches)
    priority_score = Column(Float, default=0.0, nullable=False, index=True) # computed final priority score
    upvotes_count = Column(Integer, default=0, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="questions")
    course = relationship("Course", back_populates="questions")
    cluster = relationship("QuestionCluster", back_populates="questions")
    embedding = relationship("QuestionEmbedding", uselist=False, back_populates="question", cascade="all, delete-orphan")
    file_uploads = relationship("FileUpload", back_populates="question")

    @property
    def assigned_tutor_name(self) -> Optional[str]:
        if self.cluster and self.cluster.assigned_tutor:
            tutor_user = self.cluster.assigned_tutor.user
            if tutor_user:
                return f"{tutor_user.first_name} {tutor_user.last_name}"
        return None

    @property
    def student_name(self) -> Optional[str]:
        if self.student and self.student.user:
            return self.student.user.full_name
        return None

    @property
    def student_email(self) -> Optional[str]:
        if self.student and self.student.user:
            return self.student.user.email
        return None


class QuestionEmbedding(Base):
    __tablename__ = "question_embedding"
    
    question_id = Column(UUID(as_uuid=True), ForeignKey("question.id", ondelete="CASCADE"), primary_key=True)
    # Using 384 dimensions matching Sentence-Transformer's 'all-MiniLM-L6-v2' vector size
    embedding = Column(Vector(384), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    question = relationship("Question", back_populates="embedding")


class TutorAssignment(Base):
    __tablename__ = "tutor_assignment"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("question_cluster.id", ondelete="CASCADE"), nullable=False, index=True)
    tutor_id = Column(UUID(as_uuid=True), ForeignKey("tutor.user_id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="active", nullable=False) # active, reassigned, completed
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True) # NULL means assigned by AI routing engine
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    cluster = relationship("QuestionCluster", back_populates="assignments")
    tutor = relationship("Tutor", back_populates="assignments")
    assigner = relationship("User")
