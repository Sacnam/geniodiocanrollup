"""
Sweeper task for cleaning up stuck articles (B06).
Retries articles stuck in intermediate processing states.
"""
from datetime import datetime, timedelta

from celery import shared_task
from sqlmodel import Session, select

from app.core.database import SessionLocal
from app.models.article import Article, ProcessingStatus
from app.tasks.article_tasks import (
    extract_article_task,
    generate_embedding_task,
    generate_summary_task,
    score_knowledge_delta_task,
)


@shared_task
def sweep_stuck_articles():
    """
    Find and retry articles stuck in processing for >5 minutes.
    B06: FSM-based processing with sweeper for reliability.
    """
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        
        # Find stuck articles
        stuck = db.exec(
            select(Article).where(
                Article.processing_status.in_([
                    ProcessingStatus.EXTRACTING,
                    ProcessingStatus.EMBEDDING,
                    ProcessingStatus.SCORING,
                    ProcessingStatus.SUMMARIZING,
                ]),
                Article.processing_started_at < cutoff,
                Article.processing_attempts < 3,
            )
        ).all()
        
        retried = 0
        for article in stuck:
            article.processing_attempts += 1
            db.add(article)
            db.commit()
            
            # Retry based on current status
            if article.processing_status == ProcessingStatus.EXTRACTING:
                extract_article_task.delay(article.id)
            elif article.processing_status == ProcessingStatus.EMBEDDING:
                generate_embedding_task.delay(article.id)
            elif article.processing_status == ProcessingStatus.SCORING:
                score_knowledge_delta_task.delay(article.id)
            elif article.processing_status == ProcessingStatus.SUMMARIZING:
                generate_summary_task.delay(article.id)
            
            retried += 1
        
        # Mark failed after 3 attempts
        failed = db.exec(
            select(Article).where(
                Article.processing_status.in_([
                    ProcessingStatus.EXTRACTING,
                    ProcessingStatus.EMBEDDING,
                    ProcessingStatus.SCORING,
                    ProcessingStatus.SUMMARIZING,
                ]),
                Article.processing_attempts >= 3,
            )
        ).all()
        
        for article in failed:
            article.processing_status = ProcessingStatus.EXTRACT_FAILED
            db.add(article)
        
        db.commit()
        
        return {
            "retried": retried,
            "marked_failed": len(failed),
        }
        
    finally:
        db.close()
