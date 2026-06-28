from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.api import deps
from app.models.user import User, Tutor
from app.models.question import QuestionCluster, Question, TutorAssignment
from app.models.message import ChatMessage
from app.schemas.question import (
    QuestionClusterResponse, 
    QuestionClusterDetailResponse, 
    TutorAssignmentResponse,
    TutorAssignmentCreate
)
from app.schemas.message import ChatMessageCreate, ChatMessageResponse
from app.core.ws_manager import manager

router = APIRouter(dependencies=[Depends(deps.RoleChecker(["tutor"]))])

@router.get("/clusters", response_model=List[QuestionClusterResponse])
def get_my_clusters(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve all active question clusters assigned to the logged-in tutor."""
    clusters = db.query(QuestionCluster).filter(
        QuestionCluster.assigned_tutor_id == current_user.id,
        QuestionCluster.status != "resolved"
    ).order_by(QuestionCluster.priority_score.desc()).all()
    return clusters


@router.get("/clusters/unassigned", response_model=List[QuestionClusterResponse])
def get_unassigned_clusters(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve all unassigned pending clusters for routing check."""
    clusters = db.query(QuestionCluster).filter(
        QuestionCluster.assigned_tutor_id.is_(None),
        QuestionCluster.status == "pending"
    ).order_by(QuestionCluster.priority_score.desc()).all()
    return clusters


@router.get("/clusters/{cluster_id}", response_model=QuestionClusterDetailResponse)
def get_cluster_detail(
    cluster_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve detailed overview of a cluster, including grouped questions."""
    cluster = db.query(QuestionCluster).filter(QuestionCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question cluster not found"
        )
    return cluster


@router.post("/clusters/{cluster_id}/claim", response_model=QuestionClusterResponse)
async def claim_cluster(
    cluster_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Claim responsibility for an unassigned question cluster."""
    cluster = db.query(QuestionCluster).filter(QuestionCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found"
        )
        
    if cluster.assigned_tutor_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cluster is already assigned to a tutor"
        )
        
    # Check tutor availability and workload
    tutor = db.query(Tutor).filter(Tutor.user_id == current_user.id).first()
    active_count = db.query(QuestionCluster).filter(
        QuestionCluster.assigned_tutor_id == current_user.id,
        QuestionCluster.status != "resolved"
    ).count()
    
    if active_count >= tutor.max_workload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workload limit exceeded. Maximum allowed active clusters is {tutor.max_workload}."
        )
        
    # Assign cluster
    cluster.assigned_tutor_id = current_user.id
    cluster.status = "assigned"
    
    # Audit assignment
    assignment = TutorAssignment(
        cluster_id=cluster.id,
        tutor_id=current_user.id,
        status="active",
        assigned_by=current_user.id # Self claim
    )
    db.add(assignment)
    db.commit()
    db.refresh(cluster)
    
    # Notify admins and students in real-time
    await manager.broadcast_to_cluster(
        {"event": "tutor_claimed", "cluster_id": str(cluster.id), "tutor_name": current_user.full_name},
        str(cluster.id)
    )
    
    return cluster


@router.post("/clusters/{cluster_id}/resolve", response_model=QuestionClusterResponse)
async def resolve_cluster(
    cluster_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Resolve a cluster. This marks all questions inside this cluster as resolved."""
    cluster = db.query(QuestionCluster).filter(
        QuestionCluster.id == cluster_id,
        QuestionCluster.assigned_tutor_id == current_user.id
    ).first()
    
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned cluster not found"
        )
        
    cluster.status = "resolved"
    cluster.resolved_at = datetime.utcnow()
    
    # Resolve all questions grouped inside the cluster
    for question in cluster.questions:
        question.status = "resolved"
        
    # Mark active assignment completed
    assignment = db.query(TutorAssignment).filter(
        TutorAssignment.cluster_id == cluster.id,
        TutorAssignment.tutor_id == current_user.id,
        TutorAssignment.status == "active"
    ).first()
    if assignment:
        assignment.status = "completed"
        
    db.commit()
    db.refresh(cluster)
    
    # Notify student users in real-time
    await manager.broadcast_to_cluster(
        {"event": "cluster_resolved", "cluster_id": str(cluster.id)},
        str(cluster.id)
    )
    
    return cluster


@router.post("/clusters/{cluster_id}/reassign", response_model=TutorAssignmentResponse)
async def reassign_cluster(
    cluster_id: UUID,
    assignment_in: TutorAssignmentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Reassign the cluster to another tutor."""
    cluster = db.query(QuestionCluster).filter(
        QuestionCluster.id == cluster_id,
        QuestionCluster.assigned_tutor_id == current_user.id
    ).first()
    
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned cluster not found"
        )
        
    target_tutor = db.query(Tutor).filter(Tutor.user_id == assignment_in.tutor_id).first()
    if not target_tutor or not target_tutor.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target tutor is unavailable or does not exist"
        )

    # Invalidate previous assignment
    prev_assignment = db.query(TutorAssignment).filter(
        TutorAssignment.cluster_id == cluster.id,
        TutorAssignment.tutor_id == current_user.id,
        TutorAssignment.status == "active"
    ).first()
    if prev_assignment:
        prev_assignment.status = "reassigned"
        
    # Update cluster assigned tutor
    cluster.assigned_tutor_id = target_tutor.user_id
    cluster.status = "assigned"
    
    # Create new assignment record
    new_assignment = TutorAssignment(
        cluster_id=cluster.id,
        tutor_id=target_tutor.user_id,
        status="active",
        assigned_by=current_user.id
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    
    # Broadcast updates
    await manager.broadcast_to_cluster(
        {"event": "cluster_reassigned", "cluster_id": str(cluster.id), "new_tutor_id": str(target_tutor.user_id)},
        str(cluster.id)
    )
    
    return new_assignment


@router.post("/clusters/{cluster_id}/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    cluster_id: UUID,
    message_in: ChatMessageCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Send a message to the cluster thread, broadcasting it to all active student listeners."""
    cluster = db.query(QuestionCluster).filter(QuestionCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found"
        )
        
    new_msg = ChatMessage(
        cluster_id=cluster.id,
        sender_id=current_user.id,
        content=message_in.content
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    
    # WebSocket broadcast payload
    payload = {
        "event": "new_message",
        "message": {
            "id": str(new_msg.id),
            "cluster_id": str(new_msg.cluster_id),
            "sender_id": str(new_msg.sender_id),
            "sender_name": current_user.full_name,
            "content": new_msg.content,
            "created_at": new_msg.created_at.isoformat()
        }
    }
    
    # WebSocket broadcast
    await manager.broadcast_to_cluster(payload, str(cluster.id))
    
    return new_msg
