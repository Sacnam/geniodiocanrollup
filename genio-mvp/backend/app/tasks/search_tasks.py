"""
Celery tasks for search indexing operations.
"""
import asyncio
from typing import List

from celery import shared_task
from sqlmodel import Session, select

from app.db.database import engine
from app.models.article import Article, UserArticleContext
from app.models.tag import Tag, ArticleTag
from app.services.search_service import search_service


@shared_task(bind=True, max_retries=3)
def index_article_task(self, article_id: str, user_id: str):
    """Index a single article in Elasticsearch."""
    try:
        with Session(engine) as session:
            # Get article with user context
            article = session.get(Article, article_id)
            if not article:
                return {"status": "error", "message": "Article not found"}
            
            # Get user context
            context = session.exec(
                select(UserArticleContext).where(
                    UserArticleContext.article_id == article_id,
                    UserArticleContext.user_id == user_id
                )
            ).first()
            
            # Get tags
            tag_links = session.exec(
                select(ArticleTag, Tag).join(Tag).where(
                    ArticleTag.article_id == article_id,
                    ArticleTag.user_id == user_id
                )
            ).all()
            
            tags = [{"id": tag.id, "name": tag.name, "color": tag.color}
                   for _, tag in tag_links]
            
            # Index in Elasticsearch
            result = asyncio.run(search_service.index_article(
                article_id=article.id,
                user_id=user_id,
                title=article.title or "",
                content=article.content or "",
                excerpt=article.excerpt,
                author=article.author,
                url=article.url,
                published_at=article.published_at,
                tags=tags,
                source_feed_id=article.source_feed_id,
                source_feed_title=article.source_feed_title,
                delta_score=context.delta_score if context else 0.0,
                is_read=context.is_read if context else False,
                is_favorited=getattr(context, 'is_favorited', False) if context else False
            ))
            
            return {"status": "success", "indexed": result}
            
    except Exception as exc:
        # Retry with exponential backoff
        self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)


@shared_task
def bulk_index_articles_task(article_ids: List[str], user_id: str):
    """Bulk index multiple articles."""
    results = []
    for article_id in article_ids:
        result = index_article_task.delay(article_id, user_id)
        results.append(result.id)
    
    return {"status": "started", "tasks": results, "count": len(article_ids)}


@shared_task(bind=True, max_retries=3)
def reindex_user_content(self, user_id: str):
    """Reindex all content for a user."""
    try:
        with Session(engine) as session:
            # Get all user article contexts
            contexts = session.exec(
                select(UserArticleContext, Article).join(Article).where(
                    UserArticleContext.user_id == user_id
                )
            ).all()
            
            # Queue indexing tasks in batches
            batch_size = 100
            article_ids = [article.id for context, article in contexts]
            
            for i in range(0, len(article_ids), batch_size):
                batch = article_ids[i:i + batch_size]
                bulk_index_articles_task.delay(batch, user_id)
            
            return {
                "status": "started",
                "total_articles": len(article_ids),
                "batches": (len(article_ids) + batch_size - 1) // batch_size
            }
            
    except Exception as exc:
        self.retry(countdown=300, exc=exc)


@shared_task
def delete_article_index_task(article_id: str):
    """Remove article from search index."""
    from app.core.search_config import INDEX_ARTICLES
    
    result = asyncio.run(
        search_service.delete_document(INDEX_ARTICLES, article_id)
    )
    
    return {"status": "success" if result else "failed"}


@shared_task
def update_article_read_status_task(article_id: str, user_id: str, is_read: bool):
    """Update read status in search index."""
    try:
        # Re-index the article with updated status
        result = index_article_task.delay(article_id, user_id)
        return {"status": "queued", "task_id": result.id}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@shared_task
def update_article_tags_task(article_id: str, user_id: str):
    """Update tags in search index when tags change."""
    result = index_article_task.delay(article_id, user_id)
    return {"status": "queued", "task_id": result.id}
