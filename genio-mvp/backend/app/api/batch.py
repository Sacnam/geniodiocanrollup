"""
Batch operations API for bulk actions.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.article import Article, UserArticleContext
from app.models.document import Document
from app.models.feed import Feed
from app.models.reading_list import ReadingListItem

router = APIRouter(prefix="/batch", tags=["batch"])


class BatchArticleAction(BaseModel):
    article_ids: List[str]
    action: str  # "read", "unread", "star", "unstar", "archive", "unarchive"


class BatchFeedAction(BaseModel):
    feed_ids: List[str]
    action: str  # "delete", "refresh", "mark_all_read"


class BatchDocumentAction(BaseModel):
    document_ids: List[str]
    action: str  # "delete", "add_tag", "remove_tag"
    tag: str = None


class BatchReadingListAction(BaseModel):
    item_ids: List[str]
    action: str  # "read", "unread", "archive", "delete"


@router.post("/articles")
def batch_article_action(
    request: BatchArticleAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform batch action on articles."""
    updated_count = 0
    
    for article_id in request.article_ids:
        ctx = db.exec(
            select(UserArticleContext)
            .where(
                UserArticleContext.user_id == current_user.id,
                UserArticleContext.article_id == article_id
            )
        ).first()
        
        if not ctx:
            continue
        
        if request.action == "read":
            ctx.is_read = True
        elif request.action == "unread":
            ctx.is_read = False
        elif request.action == "star":
            ctx.is_starred = True
        elif request.action == "unstar":
            ctx.is_starred = False
        elif request.action == "archive":
            ctx.is_archived = True
        elif request.action == "unarchive":
            ctx.is_archived = False
        
        db.add(ctx)
        updated_count += 1
    
    db.commit()
    
    return {
        "message": f"Updated {updated_count} articles",
        "action": request.action,
        "updated_count": updated_count
    }


@router.post("/feeds")
def batch_feed_action(
    request: BatchFeedAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform batch action on feeds."""
    processed_count = 0
    
    for feed_id in request.feed_ids:
        feed = db.exec(
            select(Feed)
            .where(
                Feed.id == feed_id,
                Feed.user_id == current_user.id
            )
        ).first()
        
        if not feed:
            continue
        
        if request.action == "delete":
            db.delete(feed)
        elif request.action == "mark_all_read":
            # Mark all articles from this feed as read
            articles = db.exec(
                select(Article.id)
                .where(Article.feed_id == feed_id)
            ).all()
            
            for article_id in articles:
                ctx = db.exec(
                    select(UserArticleContext)
                    .where(
                        UserArticleContext.user_id == current_user.id,
                        UserArticleContext.article_id == str(article_id)
                    )
                ).first()
                
                if ctx:
                    ctx.is_read = True
                    db.add(ctx)
        
        processed_count += 1
    
    db.commit()
    
    return {
        "message": f"Processed {processed_count} feeds",
        "action": request.action,
        "processed_count": processed_count
    }


@router.post("/documents")
def batch_document_action(
    request: BatchDocumentAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform batch action on documents."""
    processed_count = 0
    
    for doc_id in request.document_ids:
        doc = db.exec(
            select(Document)
            .where(
                Document.id == doc_id,
                Document.user_id == current_user.id
            )
        ).first()
        
        if not doc:
            continue
        
        if request.action == "delete":
            db.delete(doc)
        elif request.action == "add_tag" and request.tag:
            if request.tag not in doc.tags:
                doc.tags.append(request.tag)
                db.add(doc)
        elif request.action == "remove_tag" and request.tag:
            if request.tag in doc.tags:
                doc.tags.remove(request.tag)
                db.add(doc)
        
        processed_count += 1
    
    db.commit()
    
    return {
        "message": f"Processed {processed_count} documents",
        "action": request.action,
        "processed_count": processed_count
    }


@router.post("/reading-list")
def batch_reading_list_action(
    request: BatchReadingListAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform batch action on reading list items."""
    processed_count = 0
    
    for item_id in request.item_ids:
        item = db.exec(
            select(ReadingListItem)
            .where(
                ReadingListItem.id == item_id,
                ReadingListItem.user_id == current_user.id
            )
        ).first()
        
        if not item:
            continue
        
        if request.action == "read":
            item.is_read = True
            db.add(item)
        elif request.action == "unread":
            item.is_read = False
            db.add(item)
        elif request.action == "archive":
            item.is_archived = True
            db.add(item)
        elif request.action == "delete":
            db.delete(item)
        
        processed_count += 1
    
    db.commit()
    
    return {
        "message": f"Processed {processed_count} items",
        "action": request.action,
        "processed_count": processed_count
    }


@router.post("/articles/select-all-read")
def mark_all_articles_read(
    feed_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all articles as read (optionally filtered by feed)."""
    query = select(UserArticleContext).where(
        UserArticleContext.user_id == current_user.id,
        UserArticleContext.is_read == False
    )
    
    if feed_id:
        # Get articles from specific feed
        articles = db.exec(
            select(Article.id).where(Article.feed_id == feed_id)
        ).all()
        article_ids = [str(a) for a in articles]
        query = query.where(UserArticleContext.article_id.in_(article_ids))
    
    contexts = db.exec(query).all()
    
    for ctx in contexts:
        ctx.is_read = True
        db.add(ctx)
    
    db.commit()
    
    return {
        "message": f"Marked {len(contexts)} articles as read",
        "marked_count": len(contexts)
    }
