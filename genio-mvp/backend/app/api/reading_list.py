"""
Reading List API endpoints.
Save articles and web pages for later reading.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func

from app.core.database import get_session
from app.api.deps import get_current_user
from app.models.reading_list import (
    ReadingListItem,
    ReadingListItemCreate,
    ReadingListItemUpdate,
)
from app.models.user import User

router = APIRouter(prefix="/reading-list", tags=["reading-list"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_reading_list_item(
    item: ReadingListItemCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Add a new item to reading list.
    If URL already exists, updates the existing item.
    """
    # Check if URL already exists for this user
    existing = session.exec(
        select(ReadingListItem)
        .where(ReadingListItem.user_id == current_user.id)
        .where(ReadingListItem.url == item.url)
        .where(ReadingListItem.is_archived == False)
    ).first()
    
    if existing:
        # Update existing item
        existing.title = item.title
        if item.excerpt is not None:
            existing.excerpt = item.excerpt
        if item.image_url is not None:
            existing.image_url = item.image_url
        if item.source_name is not None:
            existing.source_name = item.source_name
        if item.tags is not None:
            existing.tags = item.tags
        if item.notes is not None:
            existing.notes = item.notes
        
        session.add(existing)
        session.commit()
        session.refresh(existing)
        
        return _serialize_item(existing)
    
    # Create new item
    db_item = ReadingListItem(
        user_id=current_user.id,
        url=item.url,
        title=item.title,
        excerpt=item.excerpt,
        image_url=item.image_url,
        source_name=item.source_name,
        tags=item.tags,
        notes=item.notes,
    )
    
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    
    return _serialize_item(db_item)


@router.get("")
async def list_reading_list_items(
    status: Optional[str] = Query(None, description="Filter: active, archived, read, unread"),
    search: Optional[str] = Query(None, description="Search in title and excerpt"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List user's reading list items with filtering and pagination."""
    query = select(ReadingListItem).where(ReadingListItem.user_id == current_user.id)
    
    # Apply status filter
    if status == "active":
        query = query.where(ReadingListItem.is_archived == False)
    elif status == "archived":
        query = query.where(ReadingListItem.is_archived == True)
    elif status == "read":
        query = query.where(ReadingListItem.is_read == True)
    elif status == "unread":
        query = query.where(ReadingListItem.is_read == False)
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (ReadingListItem.title.contains(search)) |
            (ReadingListItem.excerpt.contains(search))
        )
    
    # Apply tag filter
    if tag:
        query = query.where(ReadingListItem.tags.contains(tag))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()
    
    # Apply pagination and ordering
    query = query.order_by(ReadingListItem.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    items = session.exec(query).all()
    
    return {
        "items": [_serialize_item(item) for item in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.patch("/{item_id}")
async def update_reading_list_item(
    item_id: str,
    update: ReadingListItemUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Update a reading list item (mark read, archive, add notes)."""
    item = session.exec(
        select(ReadingListItem)
        .where(ReadingListItem.id == item_id)
        .where(ReadingListItem.user_id == current_user.id)
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading list item not found"
        )
    
    # Update fields
    if update.is_read is not None:
        item.is_read = update.is_read
        if update.is_read and not item.read_at:
            item.read_at = datetime.utcnow()
        elif not update.is_read:
            item.read_at = None
    
    if update.is_archived is not None:
        item.is_archived = update.is_archived
        if update.is_archived and not item.archived_at:
            item.archived_at = datetime.utcnow()
        elif not update.is_archived:
            item.archived_at = None
    
    if update.priority is not None:
        item.priority = update.priority
    
    if update.tags is not None:
        item.tags = update.tags
    
    if update.notes is not None:
        item.notes = update.notes
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    return _serialize_item(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reading_list_item(
    item_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a reading list item."""
    item = session.exec(
        select(ReadingListItem)
        .where(ReadingListItem.id == item_id)
        .where(ReadingListItem.user_id == current_user.id)
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading list item not found"
        )
    
    session.delete(item)
    session.commit()
    
    return None


@router.post("/{item_id}/extract", status_code=status.HTTP_202_ACCEPTED)
async def extract_content(
    item_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger content extraction for a reading list item.
    This is an async operation.
    """
    item = session.exec(
        select(ReadingListItem)
        .where(ReadingListItem.id == item_id)
        .where(ReadingListItem.user_id == current_user.id)
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading list item not found"
        )
    
    # TODO: Trigger extraction task
    # from app.tasks.reading_list_tasks import extract_content_task
    # extract_content_task.delay(item_id)
    
    return {"message": "Extraction started", "item_id": item_id}


def _serialize_item(item: ReadingListItem) -> dict:
    """Serialize reading list item to dict."""
    return {
        "id": item.id,
        "url": item.url,
        "title": item.title,
        "excerpt": item.excerpt,
        "image_url": item.image_url,
        "source_name": item.source_name,
        "content": item.content,
        "word_count": item.word_count,
        "is_read": item.is_read,
        "is_archived": item.is_archived,
        "priority": item.priority,
        "tags": item.tags,
        "notes": item.notes,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "read_at": item.read_at.isoformat() if item.read_at else None,
        "archived_at": item.archived_at.isoformat() if item.archived_at else None,
    }
