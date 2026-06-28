from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime
import os

from app.api import deps
from app.models.user import User, Student
from app.models.course import Course, Enrollment
from app.models.question import Question, QuestionCluster, TutorAssignment
from app.models.message import FileUpload, ChatMessage
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionResponse
from app.schemas.message import FileUploadResponse, ChatMessageCreate, ChatMessageResponse
from app.core.ws_manager import manager
from app.workers.tasks import analyze_question_task

router = APIRouter()

@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def ask_question(
    question_in: QuestionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Create a new doubt query for a course (students only)."""
    # 1. Enforce student role checks
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can ask doubts"
        )
        
    # 2. Check if course exists
    course = db.query(Course).filter(Course.id == question_in.course_id, Course.deleted_at.is_(None)).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
        
    # 3. Check student enrollment in the course
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student.user_id,
        Enrollment.course_id == course.id,
        Enrollment.status == "active"
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be enrolled in this course to post doubts"
        )

    # 4. Save question base record
    new_question = Question(
        student_id=student.user_id,
        course_id=course.id,
        title=question_in.title,
        content=question_in.content,
        status="pending",
        urgency_score=0.0,
        priority_score=0.0,
        upvotes_count=0
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    
    # 5. Dispatch background task to Celery to compute embeddings and clustering asynchronously
    try:
        analyze_question_task.delay(str(new_question.id))
    except Exception as e:
        # Gracefully log if celery/redis is offline, ensuring database transaction completes
        import logging
        logger = logging.getLogger("uvicorn.error")
        logger.error(f"Failed to queue Celery AI task: {e}")
        
    return new_question


@router.get("/{question_id}", response_model=QuestionResponse)
def get_question_details(
    question_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Fetch details of a single question."""
    question = db.query(Question).filter(
        Question.id == question_id, 
        Question.deleted_at.is_(None)
    ).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    return question


@router.put("/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: UUID,
    question_in: QuestionUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Edit title/content/status of an existing question."""
    question = db.query(Question).filter(
        Question.id == question_id, 
        Question.deleted_at.is_(None)
    ).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
        
    # Check permissions (Author, Tutor, or Admin)
    user_roles = [r.name for r in current_user.roles]
    is_author = question.student_id == current_user.id
    is_tutor_or_admin = "tutor" in user_roles or "admin" in user_roles or current_user.is_superuser
    
    if not (is_author or is_tutor_or_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this question"
        )

    # Perform updates
    update_data = question_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)
        
    db.commit()
    db.refresh(question)
    
    # Re-trigger AI analysis on edit if content changes
    if "content" in update_data or "title" in update_data:
        try:
            analyze_question_task.delay(str(question.id))
        except Exception:
            pass
            
    return question


@router.delete("/{question_id}", status_code=status.HTTP_200_OK)
def delete_question(
    question_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Soft delete a student question."""
    question = db.query(Question).filter(
        Question.id == question_id, 
        Question.deleted_at.is_(None)
    ).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    is_author = question.student_id == current_user.id
    user_roles = [r.name for r in current_user.roles]
    is_admin = "admin" in user_roles or current_user.is_superuser
    
    if not (is_author or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this question"
        )
        
    question.deleted_at = datetime.utcnow()
    db.commit()
    return {"detail": "Question deleted successfully"}


@router.post("/{question_id}/upvote", response_model=QuestionResponse)
def upvote_question(
    question_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Upvote a question. Upvoting bumps the question's urgency and priority score."""
    question = db.query(Question).filter(
        Question.id == question_id, 
        Question.deleted_at.is_(None)
    ).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
        
    question.upvotes_count += 1
    # Bumping up the priority score dynamically based on community support
    question.priority_score += 0.5
    db.commit()
    db.refresh(question)
    return question


@router.post("/{question_id}/files", response_model=FileUploadResponse)
def upload_question_screenshot(
    question_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Upload a screenshot or code error log associated with a doubt."""
    question = db.query(Question).filter(
        Question.id == question_id, 
        Question.deleted_at.is_(None)
    ).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
        
    # Standard file upload handling logic
    upload_dir = "uploads/screenshots"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_uuid = uuid4()
    extension = os.path.splitext(file.filename)[1]
    safe_filename = f"{file_uuid}{extension}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    # Read and save file content
    try:
        content = file.file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File save error: {e}"
        )
        
    file_upload = FileUpload(
        id=file_uuid,
        question_id=question.id,
        uploader_id=current_user.id,
        file_name=file.filename,
        file_type=file.content_type,
        file_path=file_path,
        file_size=len(content)
    )
    db.add(file_upload)
    db.commit()
    db.refresh(file_upload)
    return file_upload


@router.get("/clusters/{cluster_id}/messages", response_model=List[ChatMessageResponse])
def get_cluster_messages(
    cluster_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve chat history of a question cluster (accessible to enrolled students & tutors)."""
    # 1. Fetch cluster
    cluster = db.query(QuestionCluster).filter(QuestionCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found"
        )
        
    # 2. Check if student is enrolled in the course containing this cluster
    user_roles = [r.name for r in current_user.roles]
    is_tutor_or_admin = "tutor" in user_roles or "admin" in user_roles or current_user.is_superuser
    
    if not is_tutor_or_admin:
        enrollment = db.query(Enrollment).filter(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == cluster.course_id,
            Enrollment.status == "active"
        ).first()
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this course"
            )
            
    # 3. Return message history
    messages = db.query(ChatMessage).filter(
        ChatMessage.cluster_id == cluster.id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    # Map sender names
    results = []
    for msg in messages:
        results.append({
            "id": msg.id,
            "cluster_id": msg.cluster_id,
            "sender_id": msg.sender_id,
            "sender_name": msg.sender.full_name,
            "content": msg.content,
            "created_at": msg.created_at,
            "updated_at": msg.updated_at
        })
    return results


@router.post("/clusters/{cluster_id}/messages", response_model=ChatMessageResponse)
async def post_cluster_message(
    cluster_id: UUID,
    message_in: ChatMessageCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Send a chat message to a cluster thread (accessible to enrolled students & tutors)."""
    cluster = db.query(QuestionCluster).filter(QuestionCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found"
        )
        
    user_roles = [r.name for r in current_user.roles]
    is_tutor_or_admin = "tutor" in user_roles or "admin" in user_roles or current_user.is_superuser
    
    if not is_tutor_or_admin:
        enrollment = db.query(Enrollment).filter(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == cluster.course_id,
            Enrollment.status == "active"
        ).first()
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this course"
            )
            
    new_msg = ChatMessage(
        cluster_id=cluster.id,
        sender_id=current_user.id,
        content=message_in.content
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    
    # WebSocket broadcast
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
    await manager.broadcast_to_cluster(payload, str(cluster.id))
    
    return {
        "id": new_msg.id,
        "cluster_id": new_msg.cluster_id,
        "sender_id": new_msg.sender_id,
        "sender_name": current_user.full_name,
        "content": new_msg.content,
        "created_at": new_msg.created_at,
        "updated_at": new_msg.updated_at
    }
