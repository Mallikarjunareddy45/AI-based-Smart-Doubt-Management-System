from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api import deps
from app.models.user import User, Student
from app.models.course import Course, Lesson
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer
from app.schemas.quiz import (
    QuizResponse, QuizQuestionResponse,
    QuizSubmissionRequest, QuizSubmissionResponse, QuizAnswerFeedback,
    WeaknessAnalysisResponse
)
from app.ai import quiz_generator

router = APIRouter()

@router.post("/generate/lesson/{lesson_id}", response_model=QuizResponse, dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def generate_lesson_quiz(
    lesson_id: UUID,
    num_questions: int = 5,
    difficulty: str = "medium",
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Generates an AI Quiz for a specific course lesson (Instructors and Admins)."""
    try:
        quiz = quiz_generator.generate_quiz_for_lesson(db, lesson_id, num_questions, difficulty)
        return quiz
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


@router.get("/course/{course_id}", response_model=List[QuizResponse])
def get_course_quizzes(
    course_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Fetch all available quizzes for a course."""
    quizzes = db.query(Quiz).filter(Quiz.course_id == course_id).all()
    return quizzes


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz_details(
    quiz_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Fetch quiz details and questions for taking an assessment."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.post("/{quiz_id}/submit", response_model=QuizSubmissionResponse)
def submit_quiz_attempt(
    quiz_id: UUID,
    payload: QuizSubmissionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Submits student quiz attempt, computes scores, and generates detailed question feedback."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=403, detail="Only students can attempt quizzes")

    try:
        attempt = quiz_generator.evaluate_quiz_submission(
            db=db,
            student_id=student.user_id,
            quiz_id=quiz_id,
            submitted_answers=payload.answers,
            time_spent_seconds=payload.time_spent_seconds or 0
        )

        # Build detailed answer feedback list
        answer_feedbacks = []
        for ans in attempt.answers:
            q = ans.question
            answer_feedbacks.append(QuizAnswerFeedback(
                question_id=str(q.id),
                question_text=q.question_text,
                student_answer=ans.student_answer,
                correct_answer=q.correct_answer,
                is_correct=ans.is_correct,
                explanation=q.explanation,
                feedback=ans.feedback,
                concept_tag=q.concept_tag
            ))

        return QuizSubmissionResponse(
            attempt_id=str(attempt.id),
            quiz_id=str(attempt.quiz_id),
            score_percentage=attempt.score_percentage,
            points_earned=attempt.points_earned,
            total_points=attempt.total_points,
            passed=attempt.passed,
            time_spent_seconds=attempt.time_spent_seconds,
            answer_feedbacks=answer_feedbacks
        )

    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Submission evaluation failed: {str(e)}")


@router.get("/remediation/{course_id}", response_model=WeaknessAnalysisResponse)
def get_weakness_remediation(
    course_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Analyzes student quiz history in a course to identify weak concept tags and recommend lessons."""
    try:
        res = quiz_generator.analyze_student_weaknesses(db, current_user.id, course_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Remediation analysis failed: {str(e)}")


@router.post("/adaptive-practice/{course_id}", response_model=QuizResponse)
def create_adaptive_practice_session(
    course_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Generates an Adaptive AI Practice Session targeting student's weak concept topics."""
    try:
        quiz = quiz_generator.generate_adaptive_practice(db, current_user.id, course_id)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adaptive practice generation failed: {str(e)}")
