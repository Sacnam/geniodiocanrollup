"""
API endpoints for full-text search.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.models.user import User
from app.services.search_service import search_service

router = APIRouter()


@router.get("")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    type: Optional[str] = Query(None, description="Filter by type: article, document, all"),
    is_read: Optional[bool] = Query(None),
    is_favorited: Optional[bool] = Query(None),
    is_archived: Optional[bool] = Query(None),
    tags: Optional[List[str]] = Query(None),
    feeds: Optional[List[str]] = Query(None),
    author: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    delta_score_min: Optional[float] = Query(None, ge=0, le=1),
    sort_by: str = Query("relevance", regex="^(relevance|published_at|delta_score|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    highlight: bool = Query(True),
    fuzzy: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """
    Full-text search across articles and documents.
    
    Supports:
    - Phrase search with quotes: "exact phrase"
    - Boolean operators: AND, OR, NOT
    - Fuzzy matching for typos
    - Faceted filtering
    - Result highlighting
    """
    # Build filters dict
    filters = {}
    if is_read is not None:
        filters["is_read"] = is_read
    if is_favorited is not None:
        filters["is_favorited"] = is_favorited
    if is_archived is not None:
        filters["is_archived"] = is_archived
    if tags:
        filters["tags"] = tags
    if feeds:
        filters["feeds"] = feeds
    if author:
        filters["author"] = author
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if delta_score_min is not None:
        filters["delta_score_min"] = delta_score_min
    
    # Determine content types
    content_types = None
    if type and type != "all":
        content_types = [type]
    
    # Execute search
    results = await search_service.search(
        user_id=current_user.id,
        query=q,
        filters=filters if filters else None,
        content_types=content_types,
        sort_by=sort_by if sort_by != "relevance" else "relevance",
        page=page,
        per_page=per_page,
        highlight=highlight,
        fuzzy=fuzzy
    )
    
    return results


@router.get("/semantic")
async def semantic_search(
    q: str = Query(..., min_length=1, description="Natural language query"),
    is_read: Optional[bool] = Query(None),
    tags: Optional[List[str]] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    Semantic search using vector embeddings.
    
    Finds content semantically similar to the query,
    even without exact keyword matches.
    """
    filters = {}
    if is_read is not None:
        filters["is_read"] = is_read
    if tags:
        filters["tags"] = tags
    
    results = await search_service.semantic_search(
        user_id=current_user.id,
        query=q,
        filters=filters if filters else None,
        page=page,
        per_page=per_page
    )
    
    return results


@router.get("/suggest")
async def search_suggestions(
    q: str = Query(..., min_length=1, max_length=50),
    size: int = Query(10, ge=1, le=20),
    current_user: User = Depends(get_current_user)
):
    """Get autocomplete suggestions for search."""
    suggestions = await search_service.get_suggestions(
        user_id=current_user.id,
        query=q,
        size=size
    )
    
    return {"suggestions": suggestions}


@router.get("/stats")
async def search_stats(
    current_user: User = Depends(get_current_user)
):
    """Get search index statistics."""
    stats = await search_service.get_stats(user_id=current_user.id)
    return stats


@router.post("/reindex")
async def trigger_reindex(
    current_user: User = Depends(get_current_user)
):
    """
    Trigger a full reindex of user's content.
    
    This is an async operation that runs in the background.
    """
    from app.tasks.search_tasks import reindex_user_content
    
    task = reindex_user_content.delay(current_user.id)
    
    return {
        "message": "Reindex started",
        "task_id": task.id
    }
