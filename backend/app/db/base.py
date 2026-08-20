# Import all models so Alembic's env.py can read metadata dynamically
from app.db.base_class import Base  # noqa
from app.models.user import (  # noqa
    User, Role, Permission, UserSession, Student, Tutor, Admin, user_roles, role_permissions
)
from app.models.course import Course, Enrollment, Category, Section, Lesson, LessonProgress, LessonBookmark, LessonNote  # noqa
from app.models.question import (  # noqa
    Question, QuestionCluster, QuestionEmbedding, TutorAssignment
)
from app.models.message import ChatMessage, FileUpload  # noqa
from app.models.notification import Notification  # noqa
from app.models.audit import ActivityLog, AnalyticsSnapshot, Report  # noqa
from app.models.rag import LessonChunkEmbedding, AITutorConversation, AITutorMessage  # noqa
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer  # noqa
from app.models.payment import PaymentTransaction  # noqa
