from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.api import deps
from app.models.user import User
from app.models.course import Course
from app.models.audit import ActivityLog
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate

router = APIRouter()

@router.get("", response_model=List[CourseResponse])
def list_courses(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve all active courses available in the system."""
    courses = db.query(Course).filter(Course.deleted_at.is_(None)).all()
    return courses


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(deps.RoleChecker(["admin"]))])
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


@router.put("/{course_id}", response_model=CourseResponse, dependencies=[Depends(deps.RoleChecker(["admin"]))])
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


@router.delete("/{course_id}", response_model=CourseResponse, dependencies=[Depends(deps.RoleChecker(["admin"]))])
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
