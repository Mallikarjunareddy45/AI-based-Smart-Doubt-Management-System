from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from uuid import UUID

from app.api import deps
from app.models.user import User, Tutor
from app.models.question import Question, QuestionCluster
from app.models.audit import AnalyticsSnapshot, Report
from app.models.notification import Notification
from app.schemas.analytics import AnalyticsSnapshotResponse, ReportResponse, ReportCreate, NotificationResponse

router = APIRouter()

@router.get("/dashboard", response_model=dict, dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def get_live_dashboard_stats(db: Session = Depends(deps.get_db)) -> Any:
    """Retrieve active key performance indicators (KPIs) for courses workload."""
    # Active doubt counters
    total_pending = db.query(Question).filter(Question.status == "pending", Question.deleted_at.is_(None)).count()
    total_assigned = db.query(Question).filter(Question.status == "clustered", Question.deleted_at.is_(None)).count()
    total_resolved = db.query(Question).filter(Question.status == "resolved", Question.deleted_at.is_(None)).count()
    
    # Cluster counters
    active_clusters = db.query(QuestionCluster).filter(QuestionCluster.status != "resolved").count()
    resolved_clusters = db.query(QuestionCluster).filter(QuestionCluster.status == "resolved").count()
    
    # Calculate Average Resolution Wait Time in seconds (over the last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    avg_sec = db.query(
        func.avg(
            func.extract('epoch', QuestionCluster.resolved_at - QuestionCluster.created_at)
        )
    ).filter(
        QuestionCluster.status == "resolved",
        QuestionCluster.resolved_at >= seven_days_ago
    ).scalar() or 0.0
    
    # Workload balance metrics (active clusters per tutor)
    tutors = db.query(Tutor).all()
    workload_distribution = []
    for t in tutors:
        assigned_count = db.query(QuestionCluster).filter(
            QuestionCluster.assigned_tutor_id == t.user_id,
            QuestionCluster.status != "resolved"
        ).count()
        workload_distribution.append({
            "tutor_name": t.user.full_name,
            "assigned_clusters": assigned_count,
            "max_workload": t.max_workload
        })

    return {
        "questions": {
            "pending": total_pending,
            "assigned_or_clustered": total_assigned,
            "resolved": total_resolved
        },
        "clusters": {
            "active": active_clusters,
            "resolved": resolved_clusters
        },
        "average_resolution_wait_seconds": float(avg_sec),
        "tutors_workload": workload_distribution
    }


@router.get("/snapshots", response_model=List[AnalyticsSnapshotResponse], dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def get_historical_snapshots(
    course_id: Optional[UUID] = Query(None),
    metric_name: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(deps.get_db)
) -> Any:
    """Retrieve history of aggregated metric snapshots."""
    query = db.query(AnalyticsSnapshot)
    if course_id:
        query = query.filter(AnalyticsSnapshot.course_id == course_id)
    if metric_name:
        query = query.filter(AnalyticsSnapshot.metric_name == metric_name)
        
    snapshots = query.order_by(AnalyticsSnapshot.snapshot_time.desc()).limit(limit).all()
    return snapshots


@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def generate_custom_report(
    report_in: ReportCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Generate and cache a system report (e.g. course engagement levels, tutor workloads)."""
    # Compile actual metrics into report payload (Mock generation of report context)
    report_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "query_parameters": report_in.data,
        "results": {
            "average_response_rate": "84%",
            "top_busy_courses": ["CS-101", "MATH-202"],
            "tutor_coverage_efficiency": "92.5%"
        }
    }
    
    new_report = Report(
        generated_by=current_user.id,
        title=report_in.title,
        description=report_in.description,
        report_type=report_in.report_type,
        data=report_data
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report


@router.get("/notifications", response_model=List[NotificationResponse])
def get_my_notifications(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve history of notifications for the current active user."""
    notifications = db.query(Notification).filter(
        Notification.recipient_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()
    return notifications
