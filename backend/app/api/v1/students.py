from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api import deps
from app.models.user import User, Student
from app.models.course import Course, Enrollment
from app.models.question import Question
from app.schemas.course import CourseResponse, EnrollmentResponse, EnrollmentWithCourse, EnrollmentCreate
from app.schemas.question import QuestionResponse

router = APIRouter()

@router.get("/courses", response_model=List[EnrollmentWithCourse])
def get_my_enrolled_courses(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve all course enrollments for the current student."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
        
    enrollments = db.query(Enrollment).filter(
        Enrollment.student_id == student.user_id,
        Enrollment.status == "active"
    ).all()
    return enrollments


@router.get("/questions", response_model=List[QuestionResponse])
def get_my_questions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve history of doubts asked by the current student."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
        
    questions = db.query(Question).filter(
        Question.student_id == student.user_id,
        Question.deleted_at.is_(None)
    ).order_by(Question.created_at.desc()).all()
    return questions


@router.get("/courses/available", response_model=List[CourseResponse])
def get_available_courses(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve all active courses available in the system for enrollment."""
    courses = db.query(Course).filter(Course.deleted_at.is_(None)).all()
    return courses


@router.post("/courses/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_in_course(
    enrollment_in: EnrollmentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Enroll the current student in a course."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can enroll in courses"
        )
        
    course = db.query(Course).filter(Course.id == enrollment_in.course_id, Course.deleted_at.is_(None)).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
        
    # Check for existing enrollment (active or dropped)
    existing = db.query(Enrollment).filter(
        Enrollment.student_id == student.user_id,
        Enrollment.course_id == course.id
    ).first()
    
    if existing:
        if existing.status == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already actively enrolled in this course"
            )
        else:
            # Reactivate enrollment
            existing.status = "active"
            db.commit()
            db.refresh(existing)
            return existing
            
    new_enrollment = Enrollment(
        student_id=student.user_id,
        course_id=course.id,
        status="active"
    )
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    return new_enrollment
