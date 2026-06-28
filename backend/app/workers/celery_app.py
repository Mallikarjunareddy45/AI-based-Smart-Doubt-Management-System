from celery import Celery
from app.core.config import settings

# Create celery instance mapping Redis as our task broker and results registry
celery_app = Celery(
    "doubt_system_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configuration overrides
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Auto discover and import tasks from tasks file
    imports=["app.workers.tasks"]
)
