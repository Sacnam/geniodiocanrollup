"""
API endpoints for advanced tagging system.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, and_

from app.db.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.tag import (
    Tag, ArticleTag, DocumentTag, TagCreate, TagUpdate,
    TagResponse, TagCloudItem, generate_slug
)
from app.models.article import Article
from app.utils.id_generator import generate_id

router = APIRouter()


@router.post("", status_code=201, response_model=TagResponse)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new tag for the current user."""
    # Check for duplicate
    existing = session.exec(
        select(Tag).where(
            and_(Tag.user_id == current_user.id, Tag.name.ilike(tag_data.name))
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Tag with this name already exists")
    
    # Create tag
    tag = Tag(
        id=generate_id("tag"),
        user_id=current_user.id,
        name=tag_data.name,
        slug=generate_slug(tag_data.name),
        color=tag_data.color,
        icon=tag_data.icon,
        description=tag_data.description,
        parent_id=tag_data.parent_id
    )
    
    session.add(tag)
    session.commit()
    session.refresh(tag)
    
    return tag


@router.get("", response_model=List[TagResponse])
async def get_tags(
    search: Optional[str] = Query(None, description="Filter by name"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all tags for the current user."""
    query = select(Tag).where(Tag.user_id == current_user.id)
    
    if search:
        query = query.where(Tag.name.ilike(f"%{search}%"))
    
    query = query.order_by(Tag.name)
    tags = session.exec(query).all()
    
    return tags


@router.get("/autocomplete", response_model=List[TagResponse])
async def tag_autocomplete(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, le=50),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get tag suggestions for autocomplete."""
    query = select(Tag).where(
        and_(
            Tag.user_id == current_user.id,
            Tag.name.ilike(f"%{q}%")
        )
    ).order_by(Tag.usage_count.desc()).limit(limit)
    
    tags = session.exec(query).all()
    return tags


@router.get("/cloud", response_model=List[TagCloudItem])
async def get_tag_cloud(
    min_count: int = Query(1, ge=1),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get tag cloud with usage frequencies."""
    # Query to get tag counts across all content types
    query = select(
        Tag,
        func.count(ArticleTag.article_id).label("article_count")
    ).join(
        ArticleTag, Tag.id == ArticleTag.tag_id, isouter=True
    ).where(
        Tag.user_id == current_user.id
    ).group_by(Tag.id)
    
    results = session.exec(query).all()
    
    cloud_items = []
    for tag, article_count in results:
        if article_count >= min_count:
            cloud_items.append(TagCloudItem(
                id=tag.id,
                name=tag.name,
                slug=tag.slug,
                color=tag.color,
                icon=tag.icon,
                count=article_count
            ))
    
    # Sort by count descending
    cloud_items.sort(key=lambda x: x.count, reverse=True)
    
    return cloud_items


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific tag by ID."""
    tag = session.exec(
        select(Tag).where(and_(Tag.id == tag_id, Tag.user_id == current_user.id))
    ).first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return tag


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: str,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a tag."""
    tag = session.exec(
        select(Tag).where(and_(Tag.id == tag_id, Tag.user_id == current_user.id))
    ).first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    if tag.is_system:
        raise HTTPException(status_code=403, detail="Cannot modify system tags")
    
    # Update fields
    for field, value in tag_data.dict(exclude_unset=True).items():
        setattr(tag, field, value)
    
    # Regenerate slug if name changed
    if tag_data.name:
        tag.slug = generate_slug(tag_data.name)
    
    tag.updated_at = datetime.utcnow()
    
    session.add(tag)
    session.commit()
    session.refresh(tag)
    
    return tag


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a tag and remove from all items."""
    tag = session.exec(
        select(Tag).where(and_(Tag.id == tag_id, Tag.user_id == current_user.id))
    ).first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    if tag.is_system:
        raise HTTPException(status_code=403, detail="Cannot delete system tags")
    
    # Remove from all articles
    session.exec(
        select(ArticleTag).where(ArticleTag.tag_id == tag_id)
    )
    
    session.delete(tag)
    session.commit()


# Article tagging endpoints

@router.post("/articles/{article_id}/tags", status_code=201)
async def tag_article(
    article_id: str,
    tag_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Add a tag to an article."""
    # Verify tag exists and belongs to user
    tag = session.exec(
        select(Tag).where(and_(Tag.id == tag_id, Tag.user_id == current_user.id))
    ).first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Check if already tagged
    existing = session.exec(
        select(ArticleTag).where(
            and_(
                ArticleTag.article_id == article_id,
                ArticleTag.tag_id == tag_id
            )
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Article already has this tag")
    
    # Add tag
    article_tag = ArticleTag(
        article_id=article_id,
        tag_id=tag_id,
        user_id=current_user.id
    )
    
    session.add(article_tag)
    
    # Update usage count
    tag.usage_count += 1
    tag.updated_at = datetime.utcnow()
    session.add(tag)
    
    session.commit()


@router.delete("/articles/{article_id}/tags/{tag_id}", status_code=204)
async def untag_article(
    article_id: str,
    tag_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Remove a tag from an article."""
    article_tag = session.exec(
        select(ArticleTag).where(
            and_(
                ArticleTag.article_id == article_id,
                ArticleTag.tag_id == tag_id,
                ArticleTag.user_id == current_user.id
            )
        )
    ).first()
    
    if not article_tag:
        raise HTTPException(status_code=404, detail="Tag not found on article")
    
    session.delete(article_tag)
    
    # Decrement usage count
    tag = session.get(Tag, tag_id)
    if tag and tag.usage_count > 0:
        tag.usage_count -= 1
        session.add(tag)
    
    session.commit()


@router.get("/articles/{article_id}/tags", response_model=List[TagResponse])
async def get_article_tags(
    article_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all tags for an article."""
    query = select(Tag).join(
        ArticleTag, Tag.id == ArticleTag.tag_id
    ).where(
        and_(
            ArticleTag.article_id == article_id,
            ArticleTag.user_id == current_user.id
        )
    )
    
    tags = session.exec(query).all()
    return tags


# Bulk operations

class BulkTagRequest(SQLModel):
    article_ids: List[str]
    tag_id: str
    action: str  # "add" or "remove"


@router.post("/batch/articles/tags")
async def bulk_tag_articles(
    request: BulkTagRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Add or remove tags from multiple articles at once."""
    # Verify tag exists
    tag = session.exec(
        select(Tag).where(and_(Tag.id == request.tag_id, Tag.user_id == current_user.id))
    ).first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    processed = 0
    
    if request.action == "add":
        for article_id in request.article_ids:
            existing = session.exec(
                select(ArticleTag).where(
                    and_(
                        ArticleTag.article_id == article_id,
                        ArticleTag.tag_id == request.tag_id
                    )
                )
            ).first()
            
            if not existing:
                article_tag = ArticleTag(
                    article_id=article_id,
                    tag_id=request.tag_id,
                    user_id=current_user.id
                )
                session.add(article_tag)
                processed += 1
        
        # Update usage count
        tag.usage_count += processed
        
    elif request.action == "remove":
        for article_id in request.article_ids:
            article_tag = session.exec(
                select(ArticleTag).where(
                    and_(
                        ArticleTag.article_id == article_id,
                        ArticleTag.tag_id == request.tag_id,
                        ArticleTag.user_id == current_user.id
                    )
                )
            ).first()
            
            if article_tag:
                session.delete(article_tag)
                processed += 1
        
        # Update usage count
        tag.usage_count = max(0, tag.usage_count - processed)
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    session.add(tag)
    session.commit()
    
    return {"processed_count": processed}


# Import at top level for SQLModel
from sqlmodel import SQLModel
