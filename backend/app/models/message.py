import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ChatMessage(Base):
    __tablename__ = "chat_message"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("question_cluster.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(String(5000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    cluster = relationship("QuestionCluster", back_populates="messages")
    sender = relationship("User")
    file_uploads = relationship("FileUpload", back_populates="message")


class FileUpload(Base):
    __tablename__ = "file_upload"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("question.id", ondelete="CASCADE"), nullable=True, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_message.id", ondelete="CASCADE"), nullable=True, index=True)
    uploader_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False) # mime-type
    file_path = Column(String(512), nullable=False) # S3 or disk storage path
    file_size = Column(Integer, nullable=False) # in bytes
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    question = relationship("Question", back_populates="file_uploads")
    message = relationship("ChatMessage", back_populates="file_uploads")
    uploader = relationship("User")
