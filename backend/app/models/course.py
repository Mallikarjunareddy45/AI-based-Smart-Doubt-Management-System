import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Boolean, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Category(Base):
    __tablename__ = "category"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    # Relationships
    courses = relationship("Course", back_populates="category")


class Course(Base):
    __tablename__ = "course"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # SaaS Extensions
    category_id = Column(UUID(as_uuid=True), ForeignKey("category.id", ondelete="SET NULL"), nullable=True)
    instructor_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    price = Column(Float, default=0.0, nullable=False)

    # Relationships
    category = relationship("Category", back_populates="courses")
    instructor = relationship("User")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="course")
    clusters = relationship("QuestionCluster", back_populates="course")
    sections = relationship("Section", back_populates="course", cascade="all, delete-orphan", order_by="Section.order")


class Section(Base):
    __tablename__ = "section"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    order = Column(Integer, default=0, nullable=False)

    # Relationships
    course = relationship("Course", back_populates="sections")
    lessons = relationship("Lesson", back_populates="section", cascade="all, delete-orphan", order_by="Lesson.order")


class Lesson(Base):
    __tablename__ = "lesson"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("section.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    lesson_type = Column(String(50), nullable=False)  # video, pdf, notes, quiz, coding, assignment
    order = Column(Integer, default=0, nullable=False)
    
    # Lesson payload
    video_url = Column(String(512), nullable=True)
    pdf_url = Column(String(512), nullable=True)
    notes_content = Column(Text, nullable=True)
    duration_seconds = Column(Integer, default=0, nullable=False)

    # Relationships
    section = relationship("Section", back_populates="lessons")
    progress_records = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")
    bookmarks = relationship("LessonBookmark", back_populates="lesson", cascade="all, delete-orphan")
    notes = relationship("LessonNote", back_populates="lesson", cascade="all, delete-orphan")


class Enrollment(Base):
    __tablename__ = "enrollment"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.user_id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="active", nullable=False) # active, completed, dropped
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

    # Constraints
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course_enrollment"),
    )


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.user_id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lesson.id", ondelete="CASCADE"), nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    watch_time_seconds = Column(Integer, default=0, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    lesson = relationship("Lesson", back_populates="progress_records")
    student = relationship("Student")

    __table_args__ = (
        UniqueConstraint("student_id", "lesson_id", name="uq_student_lesson_progress"),
    )


class LessonBookmark(Base):
    __tablename__ = "lesson_bookmark"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.user_id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lesson.id", ondelete="CASCADE"), nullable=False)
    note = Column(String(500), nullable=True)
    timestamp_seconds = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    lesson = relationship("Lesson", back_populates="bookmarks")


class LessonNote(Base):
    __tablename__ = "lesson_note"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.user_id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lesson.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    lesson = relationship("Lesson", back_populates="notes")

    __table_args__ = (
        UniqueConstraint("student_id", "lesson_id", name="uq_student_lesson_note"),
    )
