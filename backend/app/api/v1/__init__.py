from fastapi import APIRouter
from app.api.v1 import auth, questions, students, tutors, admin, analytics, courses

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(questions.router, prefix="/questions", tags=["Questions"])
api_router.include_router(students.router, prefix="/students", tags=["Students"])
api_router.include_router(tutors.router, prefix="/tutors", tags=["Tutors"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administrator Override"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["System Analytics"])
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
