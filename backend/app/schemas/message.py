from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

# Chat Message Schemas
class ChatMessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageResponse(ChatMessageBase):
    id: UUID
    cluster_id: UUID
    sender_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# File Upload Schemas
class FileUploadResponse(BaseModel):
    id: UUID
    question_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
    uploader_id: UUID
    file_name: str
    file_type: str
    file_path: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True
