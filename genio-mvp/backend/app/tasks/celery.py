from celery import Celery
from celery.signals import task_failure, task_success

from app.core.config import settings

celery_app = Celery(
    "genio",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),
    include=[
        "app.tasks.feed_tasks",
        "app.tasks.article_tasks",
        "app.tasks.brief_tasks",
        "app.tasks.sweeper",
        "app.tasks.webhook_tasks",
    ],
)

# Configuration
celery_app.conf.update(
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.tasks.feed_tasks.*": {"queue": "feeds"},
        "app.tasks.article_tasks.*": {"queue": "articles"},
        "app.tasks.brief_tasks.*": {"queue": "briefs"},
        "app.tasks.sweeper.*": {"queue": "maintenance"},
        "app.tasks.webhook_tasks.*": {"queue": "webhooks"},
    },
    
    # Result backend
    result_expires=3600,
    result_extended=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,  # B11: Ack after task completes
    task_reject_on_worker_lost=True,
    
    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Beat schedule
    beat_schedule={
        "fetch-feeds": {
            "task": "app.tasks.feed_tasks.schedule_feed_fetches",
            "schedule": 60.0,  # Every minute
        },
        "generate-briefs": {
            "task": "app.tasks.brief_tasks.generate_daily_briefs",
            "schedule": 60.0,  # Check every minute
        },
        "sweeper": {
            "task": "app.tasks.sweeper.sweep_stuck_articles",
            "schedule": 300.0,  # Every 5 minutes (B06)
        },
    },
)


@task_success.connect
def handle_task_success(sender=None, result=None, **kwargs):
    """Handle task success."""
    pass


@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """Handle task failure - could send alert."""
    print(f"Task {task_id} failed: {exception}")


if __name__ == "__main__":
    celery_app.start()
