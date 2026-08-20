from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class CheckoutRequest(BaseModel):
    course_id: str
    amount: float
    currency: Optional[str] = "USD"
    payment_method: Optional[str] = "credit_card"

class PaymentTransactionResponse(BaseModel):
    id: str
    student_id: str
    course_id: Optional[str] = None
    amount: float
    currency: str
    payment_method: str
    transaction_id: str
    status: str
    created_at: str

class FinancialSummaryResponse(BaseModel):
    total_revenue: float
    total_transactions: int
    successful_transactions: int
    refunded_transactions: int
    currency: str
    recent_transactions: List[PaymentTransactionResponse] = []

class UserManagementUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
