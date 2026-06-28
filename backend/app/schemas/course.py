from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

# Course Schemas
class CourseBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class CourseResponse(CourseBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

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
