import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class PaymentTransaction(Base):
    __tablename__ = "payment_transaction"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.user_id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.id", ondelete="SET NULL"), nullable=True, index=True)
    
    amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), nullable=False, default="USD")
    payment_method = Column(String(50), nullable=False, default="stripe")
    transaction_id = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(String(50), nullable=False, default="succeeded") # 'succeeded', 'pending', 'failed', 'refunded'
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    student = relationship("Student")
    course = relationship("Course")
