import hashlib
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

import trafilatura
from celery import shared_task
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.qdrant import qdrant_service
from app.models.article import (
    Article,
    ArticleCluster,
    ProcessingStatus,
    UserArticleContext,
)
from app.models.feed import UserFeed
from app.services.ai_service import generate_summary, get_embedding


@shared_task(bind=True, max_retries=2)
def extract_article_task(self, article_id: str):
    """Extract article content from URL."""
    db = SessionLocal()
    try:
        article = db.get(Article, article_id)
        if not article:
            return {"status": "error", "reason": "article_not_found"}
        
        # Update status
        article.processing_status = ProcessingStatus.EXTRACTING
        article.processing_started_at = datetime.utcnow()
        db.add(article)
        db.commit()
        
        # Extract content
        try:
            downloaded = trafilatura.fetch_url(
                article.url,
                headers={"User-Agent": "GenioBot/1.0"},
            )
            
            if downloaded:
                extracted = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_tables=False,
                    deduplicate=True,
                    target_language="en",
                )
                
                if extracted and len(extracted) > settings.MIN_ARTICLE_LENGTH:
                    article.content = extracted[:settings.MAX_ARTICLE_LENGTH]
                    article.content_text = extracted[:settings.MAX_ARTICLE_LENGTH]
                    article.content_length = len(extracted)
                    
                    # Content hash for deduplication
                    article.content_hash = hashlib.sha256(
                        extracted[:1000].encode()
                    ).hexdigest()[:32]
                    
                    article.processing_status = ProcessingStatus.EXTRACTING
                    db.add(article)
                    db.commit()
                    
                    # Queue embedding
                    generate_embedding_task.delay(article_id)
                    
                    return {"status": "extracted", "length": len(extracted)}
                else:
                    article.processing_status = ProcessingStatus.EXTRACT_FAILED
                    article.last_error = "Content too short"
            else:
                article.processing_status = ProcessingStatus.EXTRACT_FAILED
                article.last_error = "Download failed"
        
        except Exception as exc:
            article.processing_status = ProcessingStatus.EXTRACT_FAILED
            article.last_error = str(exc)[:500]
            db.add(article)
            db.commit()
            raise self.retry(exc=exc, countdown=60)
        
        db.add(article)
        db.commit()
        
        return {"status": article.processing_status.value}
        
    finally:
        db.close()


@shared_task(bind=True, max_retries=2)
def generate_embedding_task(self, article_id: str):
    """Generate embedding for article and store in Qdrant."""
    db = SessionLocal()
    try:
        article = db.get(Article, article_id)
        if not article or not article.content:
            return {"status": "error", "reason": "no_content"}
        
        article.processing_status = ProcessingStatus.EMBEDDING
        db.add(article)
        db.commit()
        
        # Prepare text
        text = f"{article.title}\n\n{article.content[:4000]}"
        
        try:
            # Get embedding (B01: 1536-dim)
            embedding = get_embedding(text)
            
            # Store in Qdrant
            point = {
                "id": article_id,
                "vector": embedding,
                "payload": {
                    "article_id": article_id,
                    "feed_id": article.feed_id,
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                    "title": article.title[:200] if article.title else "",
                    "content_hash": article.content_hash,
                },
            }
            
            qdrant_service.upsert_vectors([point])
            
            article.embedding_vector_id = article_id
            article.processing_status = ProcessingStatus.EMBEDDING
            db.add(article)
            db.commit()
            
            # Queue delta scoring
            score_knowledge_delta_task.delay(article_id)
            
            return {"status": "embedded", "dimensions": len(embedding)}
            
        except Exception as exc:
            article.processing_status = ProcessingStatus.EMBED_FAILED
            article.last_error = str(exc)[:500]
            db.add(article)
            db.commit()
            raise self.retry(exc=exc, countdown=120)
        
    finally:
        db.close()


@shared_task(bind=True, max_retries=2)
def score_knowledge_delta_task(self, article_id: str):
    """
    Compute Knowledge Delta for article.
    B04: Articles are shared, delta scoring is per-user context.
    """
    db = SessionLocal()
    try:
        article = db.get(Article, article_id)
        if not article or not article.embedding_vector_id:
            return {"status": "error", "reason": "not_ready"}
        
        article.processing_status = ProcessingStatus.SCORING
        db.add(article)
        db.commit()
        
        # Find similar articles (B01: using 1536-dim vectors)
        similar = qdrant_service.search_by_article_id(
            article_id,
            limit=10,
            score_threshold=0.80,
            time_filter_days=settings.DELTA_TIME_WINDOW_DAYS,
        )
        
        # Determine cluster and delta score
        best_match = similar[0] if similar else None
        
        if best_match and best_match.score >= settings.DELTA_DUPLICATE_THRESHOLD:
            # DUPLICATE (≥0.90)
            article.cluster_id = best_match.payload.get("cluster_id") or str(uuid4())
            article.processing_status = ProcessingStatus.DUPLICATE
            delta_status = "duplicate"
            delta_score = 0.0
            
        elif best_match and best_match.score >= settings.DELTA_RELATED_THRESHOLD:
            # RELATED (≥0.85)
            article.cluster_id = best_match.payload.get("cluster_id") or str(uuid4())
            article.processing_status = ProcessingStatus.READY
            delta_status = "related"
            delta_score = 1.0 - best_match.score
            
        else:
            # NOVEL (<0.85)
            article.cluster_id = str(uuid4())
            article.processing_status = ProcessingStatus.READY
            delta_status = "novel"
            delta_score = 1.0
        
        db.add(article)
        db.commit()
        
        # Create UserArticleContext for all subscribers (B04)
        subscribers = db.exec(
            select(UserFeed).where(
                UserFeed.feed_id == article.feed_id,
                UserFeed.is_active == True,
            )
        ).all()
        
        for sub in subscribers:
            # Check if context already exists
            existing = db.exec(
                select(UserArticleContext).where(
                    UserArticleContext.user_id == sub.user_id,
                    UserArticleContext.article_id == article_id,
                )
            ).first()
            
            if not existing:
                context = UserArticleContext(
                    id=str(uuid4()),
                    user_id=sub.user_id,
                    article_id=article_id,
                    delta_score=delta_score,
                    delta_status=delta_status,
                    user_cluster_id=article.cluster_id,
                    is_read=False,
                )
                db.add(context)
        
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        
        # Queue summary generation if not duplicate
        if article.processing_status != ProcessingStatus.DUPLICATE:
            generate_summary_task.delay(article_id)
        
        return {
            "status": "scored",
            "delta_status": delta_status,
            "delta_score": delta_score,
            "cluster_id": article.cluster_id,
            "subscribers": len(subscribers),
        }
        
    finally:
        db.close()


@shared_task(bind=True, max_retries=2)
def generate_summary_task(self, article_id: str):
    """Generate AI summary for article."""
    db = SessionLocal()
    try:
        article = db.get(Article, article_id)
        if not article or article.is_duplicate:
            return {"status": "skipped", "reason": "duplicate"}
        
        # Check if already summarized
        if article.global_summary:
            return {"status": "already_summarized"}
        
        article.processing_status = ProcessingStatus.SUMMARIZING
        db.add(article)
        db.commit()
        
        try:
            # Generate summary using AI service
            summary = generate_summary(
                title=article.title or "",
                content=article.content or "",
                max_length=200,
            )
            
            article.global_summary = summary
            article.summary_generated_at = datetime.utcnow()
            article.processing_status = ProcessingStatus.READY
            
            db.add(article)
            db.commit()
            
            return {"status": "summarized", "length": len(summary)}
            
        except Exception as exc:
            article.processing_status = ProcessingStatus.SUMMARIZE_FAILED
            article.last_error = str(exc)[:500]
            db.add(article)
            db.commit()
            
            # Don't retry - summary failure is not critical
            return {"status": "failed", "error": str(exc)}
        
    finally:
        db.close()
