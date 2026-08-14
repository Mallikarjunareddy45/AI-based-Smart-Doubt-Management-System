from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID

class AIChatRequest(BaseModel):
    course_id: UUID
    query: str
    lesson_id: Optional[UUID] = None
    timestamp_seconds: Optional[int] = None
    conversation_id: Optional[UUID] = None

class CitationResponse(BaseModel):
    lesson_id: str
    lesson_title: str
    section_title: str
    chunk_type: str
    timestamp_seconds: Optional[int] = None
    snippet: str

class AIChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    query: str
    answer: str
    citations: List[CitationResponse] = []
    confidence_score: float
    can_escalate: bool

class AIEscalateRequest(BaseModel):
    message_id: UUID

class AIEscalateResponse(BaseModel):
    question_id: str
    title: str
    status: str

class IndexLessonResponse(BaseModel):
    lesson_id: str
    chunks_indexed: int
    message: str
