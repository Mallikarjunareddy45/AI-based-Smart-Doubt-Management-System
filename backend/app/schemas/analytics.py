from pydantic import BaseModel
from typing import Optional, Any, Dict
from uuid import UUID
from datetime import datetime

# Notification Schema
class NotificationResponse(BaseModel):
    id: UUID
    recipient_id: UUID
    title: str
    content: str
    type: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Activity Log Schema
class ActivityLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Analytics Snapshot Schema
class AnalyticsSnapshotResponse(BaseModel):
    id: UUID
    course_id: Optional[UUID] = None
    metric_name: str
    metric_value: float
    snapshot_time: datetime

    class Config:
        from_attributes = True

# Report Schemas
class ReportCreate(BaseModel):
    title: str
    description: Optional[str] = None
    report_type: str
    data: Dict[str, Any]

class ReportResponse(BaseModel):
    id: UUID
    generated_by: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    report_type: str
    data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
