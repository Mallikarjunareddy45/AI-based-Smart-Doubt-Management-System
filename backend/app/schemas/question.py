from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Question Base Schema
class QuestionBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    content: str = Field(..., min_length=10, max_length=10000)

class QuestionCreate(QuestionBase):
    course_id: UUID

class QuestionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    content: Optional[str] = Field(None, min_length=10, max_length=10000)
    status: Optional[str] = Field(None, pattern="^(pending|clustered|resolved)$")

# Simple user projection for Question response
class StudentSimpleResponse(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str
    
    class Config:
        from_attributes = True

class QuestionResponse(QuestionBase):
    id: UUID
    student_id: UUID
    course_id: UUID
    cluster_id: Optional[UUID] = None
    status: str
    urgency_score: float
    priority_score: float
    upvotes_count: int
    assigned_tutor_name: Optional[str] = None
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Tutor Assignment Schemas
class TutorAssignmentCreate(BaseModel):
    tutor_id: UUID

class TutorAssignmentResponse(BaseModel):
    id: UUID
    cluster_id: UUID
    tutor_id: UUID
    status: str
    assigned_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Cluster Schemas
class QuestionClusterBase(BaseModel):
    priority_score: float
    summary: Optional[str] = None
    status: str

class QuestionClusterCreate(BaseModel):
    course_id: UUID
    priority_score: float = 0.0
    summary: Optional[str] = None

class QuestionClusterUpdate(BaseModel):
    assigned_tutor_id: Optional[UUID] = None
    status: Optional[str] = Field(None, pattern="^(pending|assigned|resolved)$")
    priority_score: Optional[float] = None
    summary: Optional[str] = None

class QuestionClusterResponse(QuestionClusterBase):
    id: UUID
    course_id: UUID
    assigned_tutor_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Detail Response showing all questions nested inside the cluster
class QuestionClusterDetailResponse(QuestionClusterBase):
    id: UUID
    course_id: UUID
    assigned_tutor_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    questions: List[QuestionResponse] = []
    
    class Config:
        from_attributes = True
