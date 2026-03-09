"""
API endpoints for saved views and filters.
"""
import json
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, and_, asc

from app.db.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.saved_view import (
    SavedView, SavedViewCreate, SavedViewUpdate,
    SavedViewResponse, ReorderViewsRequest, ShareViewResponse
)
from app.utils.id_generator import generate_id
from app.utils.share_token import generate_share_token

router = APIRouter()


def parse_filters(saved_view: SavedView) -> dict:
    """Parse JSON filters from saved view."""
    try:
        return json.loads(saved_view.filters) if saved_view.filters else {}
    except json.JSONDecodeError:
        return {}


def apply_saved_view_to_query(saved_view: SavedView, query):
    """Apply saved view filters to a query."""
    filters = parse_filters(saved_view)
    
    # This is a helper that would be used in article queries
    # Returns the filter dict to be applied by the article API
    return filters


@router.post("", status_code=201, response_model=SavedViewResponse)
async def create_view(
    view_data: SavedViewCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new saved view."""
    # If setting as default, unset other defaults
    if view_data.is_default:
        existing_defaults = session.exec(
            select(SavedView).where(
                and_(
                    SavedView.user_id == current_user.id,
                    SavedView.is_default == True
                )
            )
        ).all()
        for view in existing_defaults:
            view.is_default = False
            session.add(view)
    
    # Create view
    view = SavedView(
        id=generate_id("view"),
        user_id=current_user.id,
        name=view_data.name,
        description=view_data.description,
        icon=view_data.icon,
        color=view_data.color,
        filters=json.dumps(view_data.filters) if view_data.filters else "{}",
        is_default=view_data.is_default,
        position=view_data.position
    )
    
    session.add(view)
    session.commit()
    session.refresh(view)
    
    # Return with parsed filters
    response = SavedViewResponse(
        **view.dict(),
        filters=parse_filters(view)
    )
    return response


@router.get("", response_model=List[SavedViewResponse])
async def get_views(
    include_system: bool = Query(True),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all saved views for the current user."""
    query = select(SavedView).where(
        SavedView.user_id == current_user.id
    ).order_by(asc(SavedView.position))
    
    if not include_system:
        query = query.where(SavedView.is_system == False)
    
    views = session.exec(query).all()
    
    # Parse filters for each view
    result = []
    for view in views:
        result.append(SavedViewResponse(
            **view.dict(),
            filters=parse_filters(view)
        ))
    
    return result


@router.get("/{view_id}", response_model=SavedViewResponse)
async def get_view(
    view_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific saved view."""
    view = session.exec(
        select(SavedView).where(
            and_(
                SavedView.id == view_id,
                SavedView.user_id == current_user.id
            )
        )
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    
    return SavedViewResponse(
        **view.dict(),
        filters=parse_filters(view)
    )


@router.put("/{view_id}", response_model=SavedViewResponse)
async def update_view(
    view_id: str,
    view_data: SavedViewUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a saved view."""
    view = session.exec(
        select(SavedView).where(
            and_(
                SavedView.id == view_id,
                SavedView.user_id == current_user.id
            )
        )
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    
    if view.is_system:
        raise HTTPException(status_code=403, detail="Cannot modify system views")
    
    # Handle default change
    if view_data.is_default and not view.is_default:
        existing_defaults = session.exec(
            select(SavedView).where(
                and_(
                    SavedView.user_id == current_user.id,
                    SavedView.is_default == True
                )
            )
        ).all()
        for v in existing_defaults:
            v.is_default = False
            session.add(v)
    
    # Update fields
    for field, value in view_data.dict(exclude_unset=True).items():
        if field == "filters" and value is not None:
            setattr(view, field, json.dumps(value))
        else:
            setattr(view, field, value)
    
    view.updated_at = datetime.utcnow()
    
    session.add(view)
    session.commit()
    session.refresh(view)
    
    return SavedViewResponse(
        **view.dict(),
        filters=parse_filters(view)
    )


@router.delete("/{view_id}", status_code=204)
async def delete_view(
    view_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a saved view."""
    view = session.exec(
        select(SavedView).where(
            and_(
                SavedView.id == view_id,
                SavedView.user_id == current_user.id
            )
        )
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    
    if view.is_system:
        raise HTTPException(status_code=403, detail="Cannot delete system views")
    
    session.delete(view)
    session.commit()


@router.post("/{view_id}/default", response_model=SavedViewResponse)
async def set_default_view(
    view_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Set a view as the default."""
    # Unset current default
    existing_defaults = session.exec(
        select(SavedView).where(
            and_(
                SavedView.user_id == current_user.id,
                SavedView.is_default == True
            )
        )
    ).all()
    for view in existing_defaults:
        view.is_default = False
        session.add(view)
    
    # Set new default
    view = session.exec(
        select(SavedView).where(
            and_(
                SavedView.id == view_id,
                SavedView.user_id == current_user.id
            )
        )
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    
    view.is_default = True
    view.updated_at = datetime.utcnow()
    session.add(view)
    session.commit()
    session.refresh(view)
    
    return SavedViewResponse(
        **view.dict(),
        filters=parse_filters(view)
    )


@router.put("/reorder")
async def reorder_views(
    request: ReorderViewsRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Reorder saved views."""
    for position, view_id in enumerate(request.view_ids):
        view = session.exec(
            select(SavedView).where(
                and_(
                    SavedView.id == view_id,
                    SavedView.user_id == current_user.id
                )
            )
        ).first()
        
        if view:
            view.position = position
            view.updated_at = datetime.utcnow()
            session.add(view)
    
    session.commit()
    return {"status": "ok"}


@router.post("/{view_id}/share", response_model=ShareViewResponse)
async def share_view(
    view_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Generate shareable link for a view."""
    view = session.exec(
        select(SavedView).where(
            and_(
                SavedView.id == view_id,
                SavedView.user_id == current_user.id
            )
        )
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    
    # Generate share token
    view.share_token = generate_share_token()
    view.share_enabled = True
    view.updated_at = datetime.utcnow()
    
    session.add(view)
    session.commit()
    
    # Build share URL
    from app.core.config import settings
    share_url = f"{settings.FRONTEND_URL}/shared/view/{view.share_token}"
    
    return ShareViewResponse(
        share_token=view.share_token,
        share_url=share_url
    )


@router.get("/shared/{share_token}", response_model=SavedViewResponse)
async def get_shared_view(
    share_token: str,
    session: Session = Depends(get_session)
):
    """Get a shared view by token (public endpoint)."""
    view = session.exec(
        select(SavedView).where(
            and_(
                SavedView.share_token == share_token,
                SavedView.share_enabled == True
            )
        )
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="View not found or sharing disabled")
    
    return SavedViewResponse(
        **view.dict(),
        filters=parse_filters(view)
    )
