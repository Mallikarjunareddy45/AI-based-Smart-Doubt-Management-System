from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.api import deps
from app.models.user import User, Tutor, Student
from app.models.course import Course
from app.models.question import QuestionCluster, TutorAssignment
from app.models.audit import ActivityLog
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate
from app.schemas.question import QuestionClusterResponse, TutorAssignmentResponse
from app.schemas.analytics import ActivityLogResponse
from app.core.config import settings
from app.core.ws_manager import manager

router = APIRouter(dependencies=[Depends(deps.RoleChecker(["admin"]))])

@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course_in: CourseCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Create a new course (Admin only)."""
    existing = db.query(Course).filter(Course.code == course_in.code).first()
    if existing:
        if existing.deleted_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course with this code already exists"
            )
        else:
            # Reactivate soft deleted course
            existing.deleted_at = None
            existing.title = course_in.title
            existing.description = course_in.description
            db.commit()
            db.refresh(existing)
            return existing
            
    new_course = Course(
        code=course_in.code,
        title=course_in.title,
        description=course_in.description
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    
    # Audit log
    audit = ActivityLog(
        user_id=current_user.id,
        action="create_course",
        entity_type="course",
        entity_id=new_course.id,
        payload={"code": new_course.code, "title": new_course.title}
    )
    db.add(audit)
    db.commit()
    
    return new_course


@router.put("/courses/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: UUID,
    course_in: CourseUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Update a course details (Admin only)."""
    course = db.query(Course).filter(Course.id == course_id, Course.deleted_at.is_(None)).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    update_data = course_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(course, field, update_data[field])
    db.commit()
    db.refresh(course)
    
    # Audit log
    audit = ActivityLog(
        user_id=current_user.id,
        action="update_course",
        entity_type="course",
        entity_id=course.id,
        payload=update_data
    )
    db.add(audit)
    db.commit()
    return course


@router.delete("/courses/{course_id}", response_model=CourseResponse)
def delete_course(
    course_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Soft delete a course (Admin only)."""
    course = db.query(Course).filter(Course.id == course_id, Course.deleted_at.is_(None)).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    course.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(course)
    
    # Audit log
    audit = ActivityLog(
        user_id=current_user.id,
        action="delete_course",
        entity_type="course",
        entity_id=course.id
    )
    db.add(audit)
    db.commit()
    return course


@router.get("/courses", response_model=List[CourseResponse])
def list_courses(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """List all courses in the system (Admin only)."""
    courses = db.query(Course).filter(Course.deleted_at.is_(None)).all()
    return courses


@router.get("/tutors", response_model=List[dict])
def list_tutor_workloads(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """List all tutors, their status, active cluster loads, and limits."""
    tutors = db.query(Tutor).all()
    results = []
    for tutor in tutors:
        # Count active assigned clusters
        active_clusters = db.query(QuestionCluster).filter(
            QuestionCluster.assigned_tutor_id == tutor.user_id,
            QuestionCluster.status != "resolved"
        ).count()
        
        results.append({
            "tutor_id": str(tutor.user_id),
            "email": tutor.user.email,
            "full_name": tutor.user.full_name,
            "department": tutor.department,
            "max_workload": tutor.max_workload,
            "active_clusters": active_clusters,
            "is_available": tutor.is_available,
            "created_at": tutor.created_at.isoformat()
        })
    return results


@router.put("/tutors/{tutor_id}/toggle-availability", response_model=dict)
def toggle_tutor_availability(
    tutor_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Toggle tutor availability flag (Admin only)."""
    tutor = db.query(Tutor).filter(Tutor.user_id == tutor_id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor profile not found"
        )
    tutor.is_available = not tutor.is_available
    db.commit()
    db.refresh(tutor)
    
    # Audit log
    audit = ActivityLog(
        user_id=current_user.id,
        action="toggle_tutor_availability",
        entity_type="tutor",
        entity_id=tutor.user_id,
        payload={"is_available": tutor.is_available}
    )
    db.add(audit)
    db.commit()
    
    return {"status": "success", "is_available": tutor.is_available}


@router.get("/students", response_model=List[dict])
def list_students(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve list of all students (Admin only)."""
    students = db.query(Student).all()
    return [
        {
            "student_id": str(s.user_id),
            "full_name": s.user.full_name,
            "email": s.user.email,
            "matriculation_number": s.matriculation_number,
            "enrollments_count": len(s.enrollments)
        }
        for s in students
    ]


@router.post("/clusters/{cluster_id}/assign/{tutor_id}", response_model=TutorAssignmentResponse)
async def manual_override_assignment(
    cluster_id: UUID,
    tutor_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Manually assign/override a question cluster to a specific tutor (Admin override)."""
    cluster = db.query(QuestionCluster).filter(QuestionCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question cluster not found"
        )
        
    tutor = db.query(Tutor).filter(Tutor.user_id == tutor_id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found"
        )
        
    if not tutor.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected tutor is currently unavailable"
        )

    # Invalidate current active assignment
    active_assignment = db.query(TutorAssignment).filter(
        TutorAssignment.cluster_id == cluster.id,
        TutorAssignment.status == "active"
    ).first()
    if active_assignment:
        active_assignment.status = "reassigned"

    # Set new tutor
    cluster.assigned_tutor_id = tutor.user_id
    cluster.status = "assigned"
    
    # Save assignment log marking admin ID as authorizer
    new_assignment = TutorAssignment(
        cluster_id=cluster.id,
        tutor_id=tutor.user_id,
        status="active",
        assigned_by=current_user.id
    )
    db.add(new_assignment)
    
    # Audit log override
    audit = ActivityLog(
        user_id=current_user.id,
        action="manual_override_assignment",
        entity_type="cluster",
        entity_id=cluster.id,
        payload={"tutor_id": str(tutor.user_id), "previous_tutor": str(active_assignment.tutor_id) if active_assignment else None}
    )
    db.add(audit)
    db.commit()
    db.refresh(new_assignment)
    
    # Push WS alert
    await manager.broadcast_to_cluster(
        {"event": "admin_override", "cluster_id": str(cluster.id), "tutor_name": tutor.user.full_name},
        str(cluster.id)
    )
    
    return new_assignment


@router.get("/settings", response_model=dict)
def get_ai_settings() -> Any:
    """Retrieve global AI parameters."""
    return {
        "similarity_threshold": settings.AI_SIMILARITY_THRESHOLD,
        "urgency_keywords": settings.AI_URGENCY_KEYWORDS,
        "emails_from_email": settings.EMAILS_FROM_EMAIL
    }


@router.put("/settings", response_model=dict)
def update_ai_settings(
    similarity_threshold: Optional[float] = Query(None, ge=0.0, le=1.0),
    emails_from: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Adjust system-wide configurations dynamically."""
    payload = {}
    if similarity_threshold is not None:
        settings.AI_SIMILARITY_THRESHOLD = similarity_threshold
        payload["similarity_threshold"] = similarity_threshold
    if emails_from is not None:
        settings.EMAILS_FROM_EMAIL = emails_from
        payload["emails_from_email"] = emails_from
        
    # Audit adjustment
    audit = ActivityLog(
        user_id=current_user.id,
        action="update_ai_settings",
        payload=payload
    )
    db.add(audit)
    db.commit()
    
    return {
        "similarity_threshold": settings.AI_SIMILARITY_THRESHOLD,
        "emails_from_email": settings.EMAILS_FROM_EMAIL
    }


@router.get("/logs", response_model=List[ActivityLogResponse])
def get_system_audit_logs(
    action: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(deps.get_db)
) -> Any:
    """Query system activity audit logs."""
    query = db.query(ActivityLog)
    if action:
        query = query.filter(ActivityLog.action == action)
    logs = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    return logs


# ==========================================
# SUPER ADMIN: FINANCIALS & USER MANAGEMENT
# ==========================================

from app.models.payment import PaymentTransaction
from app.models.course import Category
from app.models.rag import LessonChunkEmbedding, AITutorMessage
from app.schemas.payment import FinancialSummaryResponse, PaymentTransactionResponse, UserManagementUpdate

@router.get("/financials", response_model=FinancialSummaryResponse)
def get_financial_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve Super Admin platform revenue and financial transaction ledger."""
    transactions = db.query(PaymentTransaction).order_by(PaymentTransaction.created_at.desc()).all()
    
    total_rev = sum([t.amount for t in transactions if t.status == "succeeded"])
    succeeded_cnt = sum([1 for t in transactions if t.status == "succeeded"])
    refunded_cnt = sum([1 for t in transactions if t.status == "refunded"])

    recent_txs = [
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
        for t in transactions[:20]
    ]

    return FinancialSummaryResponse(
        total_revenue=round(total_rev, 2),
        total_transactions=len(transactions),
        successful_transactions=succeeded_cnt,
        refunded_transactions=refunded_cnt,
        currency="USD",
        recent_transactions=recent_txs
    )


@router.get("/users", response_model=List[dict])
def list_all_users(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve full searchable list of registered users and roles (Super Admin)."""
    users = db.query(User).filter(User.deleted_at.is_(None)).all()
    res = []
    for u in users:
        role_names = [r.name for r in u.roles] if u.roles else ["student"]
        res.append({
            "user_id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "roles": role_names,
            "created_at": u.created_at.isoformat()
        })
    return res


@router.put("/users/{user_id}/status", response_model=dict)
def toggle_user_status(
    user_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Suspend or activate a user account (Super Admin)."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    target.is_active = not target.is_active
    db.commit()

    audit = ActivityLog(
        user_id=current_user.id,
        action="toggle_user_status",
        entity_type="user",
        entity_id=target.id,
        payload={"is_active": target.is_active}
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "user_id": str(target.id), "is_active": target.is_active}


@router.get("/categories", response_model=List[dict])
def list_categories(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve list of all course categories."""
    categories = db.query(Category).all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "description": c.description,
            "courses_count": len(c.courses)
        }
        for c in categories
    ]


@router.post("/categories", response_model=dict)
def create_category(
    name: str,
    description: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Create a new course category (Super Admin)."""
    cat = Category(
        name=name,
        description=description
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)

    return {
        "id": str(cat.id),
        "name": cat.name,
        "description": cat.description
    }


@router.get("/ai-analytics", response_model=dict)
def get_ai_usage_analytics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve AI Token, RAG Vector Indexing, and Chat Usage Metrics (Super Admin)."""
    total_embeddings = db.query(LessonChunkEmbedding).count()
    total_ai_messages = db.query(AITutorMessage).count()
    escalated_ai_messages = db.query(AITutorMessage).filter(AITutorMessage.was_escalated == True).count()

    avg_confidence = 0.85
    msg_with_score = db.query(AITutorMessage).filter(AITutorMessage.confidence_score.isnot(None)).all()
    if msg_with_score:
        avg_confidence = round(sum([m.confidence_score for m in msg_with_score]) / len(msg_with_score), 2)

    return {
        "total_vector_embeddings": total_embeddings,
        "total_ai_chat_queries": total_ai_messages,
        "escalated_doubt_queries": escalated_ai_messages,
        "average_rag_confidence": avg_confidence,
        "embedding_model": "SentenceTransformers (all-MiniLM-L6-v2)",
        "vector_dimensions": 384
    }

