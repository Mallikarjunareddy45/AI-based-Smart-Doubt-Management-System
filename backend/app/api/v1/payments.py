import uuid
from typing import Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User, Student
from app.models.course import Course, Enrollment
from app.models.payment import PaymentTransaction
from app.models.audit import ActivityLog
from app.schemas.payment import CheckoutRequest, PaymentTransactionResponse

router = APIRouter()

@router.post("/checkout", response_model=PaymentTransactionResponse)
def process_checkout(
    payload: CheckoutRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Processes course enrollment payment and activates student access."""
    course_uuid = uuid.UUID(payload.course_id)
    course = db.query(Course).filter(Course.id == course_uuid, Course.deleted_at.is_(None)).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=400, detail="Only student accounts can purchase courses")

    # Generate unique transaction reference
    tx_ref = f"tx_live_{uuid.uuid4().hex[:12]}"

    tx = PaymentTransaction(
        student_id=current_user.id,
        course_id=course.id,
        amount=payload.amount,
        currency=payload.currency or "USD",
        payment_method=payload.payment_method or "credit_card",
        transaction_id=tx_ref,
        status="succeeded"
    )
    db.add(tx)

    # Automatically activate or update course enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == current_user.id,
        Enrollment.course_id == course.id
    ).first()

    if not enrollment:
        enrollment = Enrollment(
            student_id=current_user.id,
            course_id=course.id,
            status="active"
        )
        db.add(enrollment)
    else:
        enrollment.status = "active"

    # Log audit entry
    audit = ActivityLog(
        user_id=current_user.id,
        action="course_purchase",
        entity_type="course",
        entity_id=course.id,
        payload={"amount": payload.amount, "tx_id": tx_ref}
    )
    db.add(audit)

    db.commit()
    db.refresh(tx)

    return PaymentTransactionResponse(
        id=str(tx.id),
        student_id=str(tx.student_id),
        course_id=str(tx.course_id) if tx.course_id else None,
        amount=tx.amount,
        currency=tx.currency,
        payment_method=tx.payment_method,
        transaction_id=tx.transaction_id,
        status=tx.status,
        created_at=tx.created_at.isoformat()
    )


@router.get("/history", response_model=List[PaymentTransactionResponse])
def get_payment_history(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Fetch logged-in student's payment transaction history."""
    txs = (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.student_id == current_user.id)
        .order_by(PaymentTransaction.created_at.desc())
        .all()
    )
    return [
        PaymentTransactionResponse(
            id=str(t.id),
            student_id=str(t.student_id),
            course_id=str(t.course_id) if t.course_id else None,
            amount=t.amount,
            currency=t.currency,
            payment_method=t.payment_method,
            transaction_id=t.transaction_id,
            status=t.status,
            created_at=t.created_at.isoformat()
        )
        for t in txs
    ]
