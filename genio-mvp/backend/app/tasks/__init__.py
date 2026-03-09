"""
Celery tasks package.
Exports the celery app for worker/beat processes.
"""
from app.tasks.celery import celery_app
from app.tasks.sweeper import sweep_stuck_articles

__all__ = ["celery_app", "sweep_stuck_articles"]
