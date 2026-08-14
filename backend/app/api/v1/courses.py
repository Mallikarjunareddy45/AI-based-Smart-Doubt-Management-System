from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.api import deps
from app.models.user import User, Student
from app.models.course import Course, Enrollment, Category, Section, Lesson, LessonProgress, LessonBookmark, LessonNote
from app.models.audit import ActivityLog
from app.ai import rag_service
from app.schemas.course import (
    CourseCreate, CourseResponse, CourseUpdate, CourseDetailedResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse,
    SectionCreate, SectionUpdate, SectionResponse,
    LessonCreate, LessonUpdate, LessonResponse,
    LessonProgressUpdate, LessonProgressResponse,
    LessonBookmarkCreate, LessonBookmarkResponse,
    LessonNoteCreate, LessonNoteResponse,
    EnrollmentResponse
)

router = APIRouter()

# ==========================================
# CATEGORIES ENDPOINTS
# ==========================================

@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve all course categories."""
    return db.query(Category).all()


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(deps.RoleChecker(["admin"]))])
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Create a new course category (Admin only)."""
    existing = db.query(Category).filter(Category.name == category_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    category = Category(name=category_in.name, description=category_in.description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# ==========================================
# COURSES ENDPOINTS
# ==========================================

@router.get("", response_model=List[CourseResponse])
def list_courses(
    category_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve all published or active courses, with optional category filtering and global search."""
    query = db.query(Course).filter(Course.deleted_at.is_(None))
    
    # Non-admin/non-tutor roles can only see published courses
    user_roles = [r.name for r in current_user.roles]
    if not current_user.is_superuser and not any(r in ["admin", "tutor"] for r in user_roles):
        query = query.filter(Course.is_published == True)
        
    if category_id:
        query = query.filter(Course.category_id == category_id)
        
    if search:
        search_filter = f"%{search}%"
        query = query.filter(Course.title.ilike(search_filter) | Course.description.ilike(search_filter) | Course.code.ilike(search_filter))
        
    return query.all()


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def create_course(
    course_in: CourseCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Create a new course (Admin and Tutor/Instructor only)."""
    existing = db.query(Course).filter(Course.code == course_in.code).first()
    if existing:
        if existing.deleted_at is None:
            raise HTTPException(status_code=400, detail="Course with this code already exists")
        else:
            # Reactivate soft deleted course
            existing.deleted_at = None
            existing.title = course_in.title
            existing.description = course_in.description
            existing.category_id = course_in.category_id
            existing.instructor_id = current_user.id
            existing.price = course_in.price
            db.commit()
            db.refresh(existing)
            return existing
            
    new_course = Course(
        code=course_in.code,
        title=course_in.title,
        description=course_in.description,
        category_id=course_in.category_id,
        instructor_id=current_user.id,
        price=course_in.price,
        is_published=False
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


@router.get("/{course_id}", response_model=CourseDetailedResponse)
def get_course_details(
    course_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve details of a single course, including its syllabus (sections & lessons) and student-specific states."""
    course = db.query(Course).filter(Course.id == course_id, Course.deleted_at.is_(None)).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Check enrollment status
    enrollment = db.query(Enrollment).filter(
        Enrollment.course_id == course_id,
        Enrollment.student_id == current_user.id
    ).first()
    
    enrollment_status = enrollment.status if enrollment else None
    
    # Construct detailed response with lesson notes and progress
    sections_detailed = []
    for section in course.sections:
        lessons_detailed = []
        for lesson in section.lessons:
            # Fetch student progress
            progress = db.query(LessonProgress).filter(
                LessonProgress.lesson_id == lesson.id,
                LessonProgress.student_id == current_user.id
            ).first()
            
            # Fetch student note
            note = db.query(LessonNote).filter(
                LessonNote.lesson_id == lesson.id,
                LessonNote.student_id == current_user.id
            ).first()
            
            lessons_detailed.append({
                "id": lesson.id,
                "section_id": lesson.section_id,
                "title": lesson.title,
                "lesson_type": lesson.lesson_type,
                "order": lesson.order,
                "video_url": lesson.video_url,
                "pdf_url": lesson.pdf_url,
                "notes_content": lesson.notes_content,
                "duration_seconds": lesson.duration_seconds,
                "progress": progress,
                "note": note
            })
            
        sections_detailed.append({
            "id": section.id,
            "course_id": section.course_id,
            "title": section.title,
            "description": section.description,
            "order": section.order,
            "lessons": lessons_detailed
        })
        
    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "description": course.description,
        "category_id": course.category_id,
        "instructor_id": course.instructor_id,
        "is_published": course.is_published,
        "price": course.price,
        "created_at": course.created_at,
        "updated_at": course.updated_at,
        "category": course.category,
        "sections": sections_detailed,
        "enrollment_status": enrollment_status
    }


@router.put("/{course_id}", response_model=CourseResponse, dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def update_course(
    course_id: UUID,
    course_in: CourseUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Update a course (Admin or Instructor/Tutor who owns the course)."""
    course = db.query(Course).filter(Course.id == course_id, Course.deleted_at.is_(None)).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Check ownership
    user_roles = [r.name for r in current_user.roles]
    if not current_user.is_superuser and "admin" not in user_roles:
        if course.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="You do not have permission to modify this course")
            
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


@router.delete("/{course_id}", response_model=CourseResponse, dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def delete_course(
    course_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Soft delete a course."""
    course = db.query(Course).filter(Course.id == course_id, Course.deleted_at.is_(None)).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Check ownership
    user_roles = [r.name for r in current_user.roles]
    if not current_user.is_superuser and "admin" not in user_roles:
        if course.instructor_id != current_user.id:
            raise HTTPException(status_code=403, detail="You do not have permission to delete this course")
            
    course.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(course)
    return course


# ==========================================
# SECTIONS ENDPOINTS
# ==========================================

@router.post("/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def create_section(
    section_in: SectionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Create a new section inside a course."""
    course = db.query(Course).filter(Course.id == section_in.course_id, Course.deleted_at.is_(None)).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    new_section = Section(
        course_id=section_in.course_id,
        title=section_in.title,
        description=section_in.description,
        order=section_in.order
    )
    db.add(new_section)
    db.commit()
    db.refresh(new_section)
    return new_section


@router.put("/sections/{section_id}", response_model=SectionResponse, dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def update_section(
    section_id: UUID,
    section_in: SectionUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Update section details."""
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
        
    update_data = section_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(section, field, update_data[field])
    db.commit()
    db.refresh(section)
    return section


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def delete_section(
    section_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Response:
    """Delete a course section."""
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    db.delete(section)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==========================================
# LESSONS ENDPOINTS
# ==========================================

@router.post("/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def create_lesson(
    lesson_in: LessonCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Create a new lesson inside a section."""
    section = db.query(Section).filter(Section.id == lesson_in.section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
        
    new_lesson = Lesson(
        section_id=lesson_in.section_id,
        title=lesson_in.title,
        lesson_type=lesson_in.lesson_type,
        order=lesson_in.order,
        video_url=lesson_in.video_url,
        pdf_url=lesson_in.pdf_url,
        notes_content=lesson_in.notes_content,
        duration_seconds=lesson_in.duration_seconds
    )
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)
    
    # Trigger RAG vector indexing
    try:
        rag_service.index_lesson_content(db, new_lesson.id)
    except Exception as e:
        pass

    return new_lesson


@router.put("/lessons/{lesson_id}", response_model=LessonResponse, dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def update_lesson(
    lesson_id: UUID,
    lesson_in: LessonUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Update lesson parameters (video URL, notes content, etc.)."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
        
    update_data = lesson_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(lesson, field, update_data[field])
    db.commit()
    db.refresh(lesson)

    # Trigger RAG vector re-indexing
    try:
        rag_service.index_lesson_content(db, lesson.id)
    except Exception as e:
        pass

    return lesson


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(deps.RoleChecker(["admin", "tutor"]))])
def delete_lesson(
    lesson_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Response:
    """Delete a lesson."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    db.delete(lesson)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==========================================
# STUDENT ACTIONS: ENROLLMENT & INTERACTIVES
# ==========================================

@router.post("/{course_id}/enroll", response_model=EnrollmentResponse)
def enroll_course(
    course_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Enroll a student in a course."""
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id, Course.deleted_at.is_(None)).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Verify student profile exists
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=400, detail="Only students can enroll in courses")
        
    # Check if already enrolled
    existing = db.query(Enrollment).filter(
        Enrollment.student_id == current_user.id,
        Enrollment.course_id == course_id
    ).first()
    if existing:
        if existing.status == "active":
            return existing
        existing.status = "active"
        db.commit()
        db.refresh(existing)
        return existing
        
    new_enrollment = Enrollment(
        student_id=current_user.id,
        course_id=course_id,
        status="active"
    )
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    return new_enrollment


@router.post("/lessons/{lesson_id}/progress", response_model=LessonProgressResponse)
def update_lesson_progress(
    lesson_id: UUID,
    progress_in: LessonProgressUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Save progress for a lesson (completion status and watch time)."""
    # Verify lesson
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
        
    progress = db.query(LessonProgress).filter(
        LessonProgress.lesson_id == lesson_id,
        LessonProgress.student_id == current_user.id
    ).first()
    
    now = datetime.utcnow()
    if not progress:
        progress = LessonProgress(
            student_id=current_user.id,
            lesson_id=lesson_id,
            is_completed=progress_in.is_completed,
            watch_time_seconds=progress_in.watch_time_seconds,
            completed_at=now if progress_in.is_completed else None
        )
        db.add(progress)
    else:
        progress.is_completed = progress_in.is_completed
        progress.watch_time_seconds = progress_in.watch_time_seconds
        if progress_in.is_completed and not progress.completed_at:
            progress.completed_at = now
        elif not progress_in.is_completed:
            progress.completed_at = None
            
    db.commit()
    db.refresh(progress)
    return progress


@router.get("/lessons/{lesson_id}/bookmarks", response_model=List[LessonBookmarkResponse])
def get_lesson_bookmarks(
    lesson_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Fetch all bookmarks created by the student for this lesson."""
    return db.query(LessonBookmark).filter(
        LessonBookmark.lesson_id == lesson_id,
        LessonBookmark.student_id == current_user.id
    ).all()


@router.post("/lessons/{lesson_id}/bookmarks", response_model=LessonBookmarkResponse, status_code=status.HTTP_201_CREATED)
def create_lesson_bookmark(
    lesson_id: UUID,
    bookmark_in: LessonBookmarkCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Bookmark a specific timestamp in a video lesson or note."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
        
    bookmark = LessonBookmark(
        student_id=current_user.id,
        lesson_id=lesson_id,
        note=bookmark_in.note,
        timestamp_seconds=bookmark_in.timestamp_seconds
    )
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark


@router.delete("/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson_bookmark(
    bookmark_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Response:
    """Delete a lesson bookmark."""
    bookmark = db.query(LessonBookmark).filter(
        LessonBookmark.id == bookmark_id,
        LessonBookmark.student_id == current_user.id
    ).first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    db.delete(bookmark)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/lessons/{lesson_id}/notes", response_model=Optional[LessonNoteResponse])
def get_lesson_note(
    lesson_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Fetch the student's study notes for this lesson."""
    return db.query(LessonNote).filter(
        LessonNote.lesson_id == lesson_id,
        LessonNote.student_id == current_user.id
    ).first()


@router.post("/lessons/{lesson_id}/notes", response_model=LessonNoteResponse)
def save_lesson_note(
    lesson_id: UUID,
    note_in: LessonNoteCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Save or update study notes for a lesson."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
        
    note = db.query(LessonNote).filter(
        LessonNote.lesson_id == lesson_id,
        LessonNote.student_id == current_user.id
    ).first()
    
    if not note:
        note = LessonNote(
            student_id=current_user.id,
            lesson_id=lesson_id,
            content=note_in.content
        )
        db.add(note)
    else:
        note.content = note_in.content
        note.updated_at = datetime.utcnow()
        
    db.commit()
    db.refresh(note)
    return note
