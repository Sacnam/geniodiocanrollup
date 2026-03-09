"""
Reading List / Watch Later API
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.reading_list import (
    ReadingListItem,
    ReadingListItemCreate,
    ReadingListItemUpdate,
)
from app.models.user import User
from app.services.content_extractor import extract_article_content

router = APIRouter()


@router.post("/save", response_model=ReadingListItem, status_code=status.HTTP_201_CREATED)
async def save_to_reading_list(
    item: ReadingListItemCreate,
    extract_content: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save an article/page to reading list."""
    
    # Check if already saved
    existing = db.query(ReadingListItem).filter(
        ReadingListItem.user_id == current_user.id,
        ReadingListItem.url == item.url,
        ReadingListItem.is_archived == False
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item already in reading list"
        )
    
    # Extract content if requested
    content = None
    word_count = None
    if extract_content:
        try:
            extracted = await extract_article_content(item.url)
            content = extracted.get("content")
            word_count = len(content.split()) if content else None
        except Exception:
            pass  # Fail silently, save without content
    
    # Create item
    db_item = ReadingListItem(
        user_id=current_user.id,
        url=item.url,
        title=item.title,
        excerpt=item.excerpt,
        image_url=item.image_url,
        source_name=item.source_name,
        content=content,
        word_count=word_count,
        tags=item.tags,
        notes=item.notes,
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item


@router.get("/list", response_model=List[ReadingListItem])
def get_reading_list(
    filter: str = Query("all", enum=["all", "unread", "read", "archived"]),
    tag: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's reading list."""
    
    query = db.query(ReadingListItem).filter(
        ReadingListItem.user_id == current_user.id
    )
    
    # Apply filters
    if filter == "unread":
        query = query.filter(ReadingListItem.is_read == False, ReadingListItem.is_archived == False)
    elif filter == "read":
        query = query.filter(ReadingListItem.is_read == True, ReadingListItem.is_archived == False)
    elif filter == "archived":
        query = query.filter(ReadingListItem.is_archived == True)
    else:  # all
        query = query.filter(ReadingListItem.is_archived == False)
    
    if tag:
        query = query.filter(ReadingListItem.tags.contains(tag))
    
    if search:
        query = query.filter(
            ReadingListItem.title.contains(search) |
            ReadingListItem.excerpt.contains(search) |
            ReadingListItem.notes.contains(search)
        )
    
    # Order by priority desc, then created_at desc
    query = query.order_by(desc(ReadingListItem.priority), desc(ReadingListItem.created_at))
    
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    
    return items


@router.patch("/{item_id}", response_model=ReadingListItem)
def update_reading_list_item(
    item_id: str,
    updates: ReadingListItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a reading list item (mark read, archive, add notes)."""
    
    item = db.query(ReadingListItem).filter(
        ReadingListItem.id == item_id,
        ReadingListItem.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    # Update fields
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(item, field, value)
        
        # Set timestamps for state changes
        if field == "is_read" and value == True:
            item.read_at = datetime.utcnow()
        elif field == "is_archived" and value == True:
            item.archived_at = datetime.utcnow()
    
    db.commit()
    db.refresh(item)
    
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reading_list_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete item from reading list."""
    
    item = db.query(ReadingListItem).filter(
        ReadingListItem.id == item_id,
        ReadingListItem.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    db.delete(item)
    db.commit()
    
    return None


@router.post("/{item_id}/extract")
async def extract_item_content(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Extract and save full content for an item."""
    
    item = db.query(ReadingListItem).filter(
        ReadingListItem.id == item_id,
        ReadingListItem.user_id == current_user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    try:
        extracted = await extract_article_content(item.url)
        item.content = extracted.get("content")
        item.word_count = len(item.content.split()) if item.content else None
        db.commit()
        
        return {"status": "success", "word_count": item.word_count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract content: {str(e)}"
        )


@router.get("/stats")
def get_reading_list_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get reading list statistics."""
    
    total = db.query(ReadingListItem).filter(
        ReadingListItem.user_id == current_user.id,
        ReadingListItem.is_archived == False
    ).count()
    
    unread = db.query(ReadingListItem).filter(
        ReadingListItem.user_id == current_user.id,
        ReadingListItem.is_read == False,
        ReadingListItem.is_archived == False
    ).count()
    
    archived = db.query(ReadingListItem).filter(
        ReadingListItem.user_id == current_user.id,
        ReadingListItem.is_archived == True
    ).count()
    
    return {
        "total": total,
        "unread": unread,
        "read": total - unread,
        "archived": archived
    }
