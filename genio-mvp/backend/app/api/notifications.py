"""
Notifications API endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.models.user import User
from app.services.notification_service import notification_service, NotificationType

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[dict])
def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get user's notifications."""
    return notification_service.get_notifications(
        user_id=str(current_user.id),
        unread_only=unread_only,
        limit=limit
    )


@router.get("/count")
def get_unread_count(
    current_user: User = Depends(get_current_user)
):
    """Get unread notification count."""
    count = notification_service.get_unread_count(str(current_user.id))
    return {"count": count}


@router.post("/{notification_id}/read")
def mark_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read."""
    notification_service.mark_as_read(str(current_user.id), notification_id)
    return {"message": "Marked as read"}


@router.post("/read-all")
def mark_all_as_read(
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read."""
    notification_service.mark_all_as_read(str(current_user.id))
    return {"message": "All marked as read"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete notification."""
    # TODO: Implement delete
    return {"message": "Notification deleted"}
