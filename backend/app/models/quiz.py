import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Boolean, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Quiz(Base):
    __tablename__ = "quiz"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(UUID(as_uuid=True), ForeignKey("section.id", ondelete="SET NULL"), nullable=True, index=True)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lesson.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    passing_score_percentage = Column(Float, nullable=False, default=70.0)
    time_limit_minutes = Column(Integer, nullable=True)
    is_ai_generated = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    course = relationship("Course")
    section = relationship("Section")
    lesson = relationship("Lesson")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_question"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quiz.id", ondelete="CASCADE"), nullable=False, index=True)
    
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False, default="multiple_choice") # 'multiple_choice', 'true_false', 'short_answer'
    options = Column(JSON().with_variant(JSONB(astext_type=Text()), "postgresql"), nullable=True) # Array of option strings
    correct_answer = Column(String(500), nullable=False)
    explanation = Column(Text, nullable=True)
    concept_tag = Column(String(255), nullable=False, default="General Concept", index=True)
    points = Column(Integer, nullable=False, default=1)
    order = Column(Integer, nullable=False, default=1)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("QuizAnswer", back_populates="question", cascade="all, delete-orphan")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempt"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quiz.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    score_percentage = Column(Float, nullable=False, default=0.0)
    points_earned = Column(Integer, nullable=False, default=0)
    total_points = Column(Integer, nullable=False, default=0)
    passed = Column(Boolean, nullable=False, default=False)
    time_spent_seconds = Column(Integer, nullable=False, default=0)
    
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("Student")
    answers = relationship("QuizAnswer", back_populates="attempt", cascade="all, delete-orphan")


class QuizAnswer(Base):
    __tablename__ = "quiz_answer"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(UUID(as_uuid=True), ForeignKey("quiz_attempt.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("quiz_question.id", ondelete="CASCADE"), nullable=False, index=True)
    
    student_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=False, default=False)
    feedback = Column(Text, nullable=True)

    # Relationships
    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("QuizQuestion", back_populates="answers")
