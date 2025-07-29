from celery import Celery
from app.core.config import SESSION_DB_URL

# Initialize the Celery app instance.
# The first argument is the name of the current module.
# The 'broker' and 'backend' arguments point to your Redis instance.
# The 'include' argument tells Celery which modules contain your task definitions.
celery_app = Celery(
    "tasks",
    broker=SESSION_DB_URL,
    backend=SESSION_DB_URL,
    include=["app.workers.tasks"]
)

# Optional configuration for better serialization and timezone handling.
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
