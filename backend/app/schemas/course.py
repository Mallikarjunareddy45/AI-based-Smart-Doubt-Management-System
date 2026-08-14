from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Category Schemas
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)

class CategoryResponse(CategoryBase):
    id: UUID

    class Config:
        from_attributes = True


# Lesson Schemas
class LessonBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    lesson_type: str = Field(..., pattern="^(video|pdf|notes|quiz|coding|assignment)$")
    order: int = Field(default=0, ge=0)
    video_url: Optional[str] = Field(None, max_length=512)
    pdf_url: Optional[str] = Field(None, max_length=512)
    notes_content: Optional[str] = Field(None)
    duration_seconds: int = Field(default=0, ge=0)

class LessonCreate(LessonBase):
    section_id: UUID

class LessonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    lesson_type: Optional[str] = Field(None, pattern="^(video|pdf|notes|quiz|coding|assignment)$")
    order: Optional[int] = Field(None, ge=0)
    video_url: Optional[str] = Field(None, max_length=512)
    pdf_url: Optional[str] = Field(None, max_length=512)
    notes_content: Optional[str] = Field(None)
    duration_seconds: Optional[int] = Field(None, ge=0)

class LessonResponse(LessonBase):
    id: UUID
    section_id: UUID

    class Config:
        from_attributes = True


# Section Schemas
class SectionBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    order: int = Field(default=0, ge=0)

class SectionCreate(SectionBase):
    course_id: UUID

class SectionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    order: Optional[int] = Field(None, ge=0)

class SectionResponse(SectionBase):
    id: UUID
    course_id: UUID
    lessons: List[LessonResponse] = []

    class Config:
        from_attributes = True


# Course Schemas
class CourseBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class CourseCreate(CourseBase):
    category_id: Optional[UUID] = None
    price: float = Field(default=0.0, ge=0.0)

class CourseUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[UUID] = None
    instructor_id: Optional[UUID] = None
    is_published: Optional[bool] = None
    price: Optional[float] = Field(None, ge=0.0)

class CourseResponse(CourseBase):
    id: UUID
    category_id: Optional[UUID]
    instructor_id: Optional[UUID]
    is_published: bool
    price: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Lesson Progress Schemas
class LessonProgressUpdate(BaseModel):
    is_completed: bool
    watch_time_seconds: int = Field(default=0, ge=0)

class LessonProgressResponse(BaseModel):
    id: UUID
    student_id: UUID
    lesson_id: UUID
    is_completed: bool
    watch_time_seconds: int
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Lesson Bookmark Schemas
class LessonBookmarkCreate(BaseModel):
    note: Optional[str] = Field(None, max_length=500)
    timestamp_seconds: int = Field(default=0, ge=0)

class LessonBookmarkResponse(BaseModel):
    id: UUID
    student_id: UUID
    lesson_id: UUID
    note: Optional[str]
    timestamp_seconds: int
    created_at: datetime

    class Config:
        from_attributes = True


# Lesson Note Schemas
class LessonNoteCreate(BaseModel):
    content: str

class LessonNoteResponse(BaseModel):
    id: UUID
    student_id: UUID
    lesson_id: UUID
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Detailed Course Syllabus Schema for Students
class LessonWithProgressResponse(LessonResponse):
    progress: Optional[LessonProgressResponse] = None
    note: Optional[LessonNoteResponse] = None

class SectionWithProgressResponse(SectionBase):
    id: UUID
    course_id: UUID
    lessons: List[LessonWithProgressResponse] = []

class CourseDetailedResponse(CourseResponse):
    category: Optional[CategoryResponse] = None
    sections: List[SectionWithProgressResponse] = []
    enrollment_status: Optional[str] = None  # active, completed, dropped, or null if not enrolled

    class Config:
        from_attributes = True


# Enrollment Schemas
class EnrollmentCreate(BaseModel):
    course_id: UUID

class EnrollmentUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|completed|dropped)$")

class EnrollmentResponse(BaseModel):
    id: UUID
    student_id: UUID
    course_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
class EnrollmentWithCourse(EnrollmentResponse):
    course: CourseResponse
    
    class Config:
        from_attributes = True
