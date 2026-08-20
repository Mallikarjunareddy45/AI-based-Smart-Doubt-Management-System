from fastapi import APIRouter
from app.api.v1 import auth, questions, students, tutors, admin, analytics, courses, ai_tutor, quizzes, payments

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(questions.router, prefix="/questions", tags=["Questions"])
api_router.include_router(students.router, prefix="/students", tags=["Students"])
api_router.include_router(tutors.router, prefix="/tutors", tags=["Tutors"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administrator Override"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["System Analytics"])
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(ai_tutor.router, prefix="/ai-tutor", tags=["AI Tutor RAG Engine"])
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["Quiz & Adaptive Practice Engine"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payment & Financial Ledger Engine"])
