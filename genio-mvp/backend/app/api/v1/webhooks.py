"""
Webhook Management API
"""
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.observability import MetricsManager
from app.models.user import User

router = APIRouter()
metrics = MetricsManager()


class WebhookEventType(str):
    """Webhook event types."""
    ARTICLE_READY = "article.ready"
    BRIEF_DELIVERED = "brief.delivered"
    DOCUMENT_PROCESSED = "document.processed"
    SCOUT_INSIGHT = "scout.insight"
    USER_MENTIONED = "user.mentioned"
    SYSTEM_ALERT = "system.alert"


class WebhookBase(BaseModel):
    """Base webhook model."""
    url: HttpUrl
    events: List[str] = Field(..., description="Events to subscribe to")
    description: Optional[str] = None
    secret: Optional[str] = Field(None, description="Secret for HMAC signature")


class WebhookCreate(WebhookBase):
    pass


class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WebhookResponse(WebhookBase):
    """Webhook response model."""
    id: str
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime] = None
    failure_count: int = 0

    class Config:
        from_attributes = True


class WebhookDelivery(BaseModel):
    """Webhook delivery record."""
    id: str
    webhook_id: str
    event_type: str
    payload: Dict[str, Any]
    status: str  # pending, delivered, failed
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    attempt_count: int = 0
    created_at: datetime
    delivered_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None


class WebhookManager:
    """Central webhook management."""
    
    def __init__(self):
        self._webhooks: Dict[str, List[Dict]] = {}  # event -> list of webhooks
        self._max_retries = 5
        self._retry_delays = [5, 30, 300, 1800, 3600]  # seconds
    
    def register_webhook(self, webhook: Dict[str, Any]):
        """Register a webhook for events."""
        for event in webhook["events"]:
            if event not in self._webhooks:
                self._webhooks[event] = []
            self._webhooks[event].append(webhook)
    
    def unregister_webhook(self, webhook_id: str):
        """Remove a webhook."""
        for event, hooks in self._webhooks.items():
            self._webhooks[event] = [h for h in hooks if h["id"] != webhook_id]
    
    async def trigger_event(self, event_type: str, payload: Dict[str, Any],
                           user_id: Optional[str] = None):
        """
        Trigger a webhook event.
        
        Args:
            event_type: Type of event
            payload: Event data
            user_id: Optional user filter (None = all)
        """
        webhooks = self._webhooks.get(event_type, [])
        
        for webhook in webhooks:
            if not webhook.get("is_active", True):
                continue
            
            # Filter by user if specified
            if user_id and webhook.get("user_id") != user_id:
                continue
            
            # Queue delivery task
            await self._queue_delivery(webhook, event_type, payload)
        
        # Track event
        metrics.increment("webhook.event_triggered", tags={"event": event_type})
    
    async def _queue_delivery(self, webhook: Dict, event_type: str, 
                              payload: Dict[str, Any]):
        """Queue webhook delivery task."""
        from app.tasks.webhook_tasks import deliver_webhook
        
        delivery_id = f"delivery_{datetime.utcnow().timestamp()}"
        
        # Add metadata to payload
        full_payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload,
        }
        
        # Queue Celery task
        deliver_webhook.delay(
            webhook_id=webhook["id"],
            delivery_id=delivery_id,
            url=str(webhook["url"]),
            payload=full_payload,
            secret=webhook.get("secret"),
        )
    
    def generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        signature = hmac.new(
            secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def verify_signature(self, payload: bytes, signature: str, 
                         secret: str) -> bool:
        """Verify webhook signature."""
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)


# Global instance
_webhook_manager = None


def get_webhook_manager() -> WebhookManager:
    """Get webhook manager instance."""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
def create_webhook(
    webhook_in: WebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new webhook subscription."""
    # Validate events
    valid_events = [
        "article.ready", "brief.delivered", "document.processed",
        "scout.insight", "user.mentioned", "system.alert"
    ]
    for event in webhook_in.events:
        if event not in valid_events and not event.endswith(".*"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type: {event}"
            )
    
    webhook = WebhookResponse(
        id=f"wh_{datetime.utcnow().timestamp()}",
        user_id=current_user.id,
        url=webhook_in.url,
        events=webhook_in.events,
        description=webhook_in.description,
        secret=webhook_in.secret or secrets.token_urlsafe(32),
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    # Register in manager
    manager = get_webhook_manager()
    manager.register_webhook(webhook.dict())
    
    metrics.increment("webhook.created")
    return webhook


@router.get("/", response_model=List[WebhookResponse])
def list_webhooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's webhooks."""
    # Would query database in real implementation
    return []


@router.get("/{webhook_id}", response_model=WebhookResponse)
def get_webhook(
    webhook_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get webhook details."""
    raise HTTPException(status_code=404, detail="Not implemented")


@router.patch("/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    webhook_id: str,
    webhook_in: WebhookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update webhook."""
    raise HTTPException(status_code=404, detail="Not implemented")


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(
    webhook_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete webhook."""
    manager = get_webhook_manager()
    manager.unregister_webhook(webhook_id)
    
    metrics.increment("webhook.deleted")
    return None


@router.post("/{webhook_id}/test")
def test_webhook(
    webhook_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send test webhook."""
    manager = get_webhook_manager()
    
    asyncio.create_task(manager.trigger_event(
        "system.alert",
        {"message": "This is a test webhook", "webhook_id": webhook_id},
        current_user.id
    ))
    
    return {"status": "Test webhook queued"}


@router.post("/{webhook_id}/rotate-secret", response_model=WebhookResponse)
def rotate_secret(
    webhook_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rotate webhook secret."""
    import secrets
    
    new_secret = secrets.token_urlsafe(32)
    # Would update in database
    
    return {"status": "Secret rotated", "new_secret": new_secret}


import asyncio  # noqa: E402
import secrets  # noqa: E402
