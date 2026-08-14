from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api import deps
from app.models.user import User, Student
from app.models.course import Course, Lesson
from app.schemas.ai_tutor import (
    AIChatRequest, AIChatResponse,
    AIEscalateRequest, AIEscalateResponse,
    IndexLessonResponse
)
from app.ai import rag_service

router = APIRouter()

@router.post("/chat", response_model=AIChatResponse)
def ai_tutor_chat(
    payload: AIChatRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """RAG AI Tutor chat endpoint supporting course knowledge search and video timestamp context."""
    # Verify course exists
    course = db.query(Course).filter(Course.id == payload.course_id, Course.deleted_at.is_(None)).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    try:
        response = rag_service.generate_tutor_response(
            db=db,
            student_id=current_user.id,
            course_id=payload.course_id,
            query_text=payload.query,
            lesson_id=payload.lesson_id,
            timestamp_seconds=payload.timestamp_seconds,
            conversation_id=payload.conversation_id
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Tutor query failed: {str(e)}")


@router.post("/index-lesson/{lesson_id}", response_model=IndexLessonResponse, dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def index_lesson_content(
    lesson_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Re-indexes a lesson's notes/metadata into vector embeddings (Instructors and Admins)."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    count = rag_service.index_lesson_content(db, lesson_id)
    return {
        "lesson_id": str(lesson_id),
        "chunks_indexed": count,
        "message": f"Successfully indexed {count} vector embeddings for lesson '{lesson.title}'."
    }


@router.post("/escalate", response_model=AIEscalateResponse)
def escalate_ai_message(
    payload: AIEscalateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Escalates a low-confidence AI message into an active student doubt question for human instructors."""
    try:
        res = rag_service.escalate_to_instructor(db, current_user.id, payload.message_id)
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Escalation failed: {str(e)}")
