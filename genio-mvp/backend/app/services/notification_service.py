"""
Notification service for real-time updates.
Uses WebSocket for real-time and prepares for push notifications.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
import structlog

from app.core.redis import redis_client
from app.realtime.websocket import connection_manager

logger = structlog.get_logger()


class NotificationType(str, Enum):
    """Types of notifications."""
    ARTICLE_READY = "article_ready"
    BRIEF_READY = "brief_ready"
    DOCUMENT_PROCESSED = "document_processed"
    SCOUT_FINDING = "scout_finding"
    SCOUT_INSIGHT = "scout_insight"
    SYSTEM = "system"
    BUDGET_WARNING = "budget_warning"


class NotificationPriority(str, Enum):
    """Priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NotificationService:
    """Service for managing notifications."""
    
    def __init__(self):
        self.redis = redis_client
    
    async def send_notification(
        self,
        user_id: str,
        type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[dict] = None,
        link: Optional[str] = None
    ):
        """
        Send notification to user via WebSocket and store for later.
        
        Args:
            user_id: Target user
            type: Notification type
            title: Notification title
            message: Notification body
            priority: Priority level
            data: Additional data
            link: Deep link
        """
        notification = {
            "id": f"{user_id}:{datetime.utcnow().timestamp()}",
            "user_id": user_id,
            "type": type.value,
            "title": title,
            "message": message,
            "priority": priority.value,
            "data": data or {},
            "link": link,
            "created_at": datetime.utcnow().isoformat(),
            "read": False,
        }
        
        # Store in Redis for persistence
        key = f"notifications:{user_id}"
        self.redis.lpush(key, notification)
        self.redis.ltrim(key, 0, 99)  # Keep last 100
        
        # Send real-time via WebSocket
        await connection_manager.send_to_user(
            user_id,
            {
                "type": "notification",
                "payload": notification
            }
        )
        
        # TODO: Send push notification if user has enabled
        # await self._send_push_notification(user_id, notification)
        
        logger.info(
            "Notification sent",
            user_id=user_id,
            type=type.value,
            title=title
        )
    
    def get_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[dict]:
        """Get user's notifications."""
        key = f"notifications:{user_id}"
        notifications = self.redis.lrange(key, 0, limit - 1)
        
        if unread_only:
            notifications = [n for n in notifications if not n.get("read")]
        
        return notifications
    
    def mark_as_read(self, user_id: str, notification_id: str):
        """Mark notification as read."""
        key = f"notifications:{user_id}"
        notifications = self.redis.lrange(key, 0, -1)
        
        for i, notif in enumerate(notifications):
            if notif.get("id") == notification_id:
                notif["read"] = True
                self.redis.lset(key, i, notif)
                break
    
    def mark_all_as_read(self, user_id: str):
        """Mark all notifications as read."""
        key = f"notifications:{user_id}"
        notifications = self.redis.lrange(key, 0, -1)
        
        for i, notif in enumerate(notifications):
            notif["read"] = True
            self.redis.lset(key, i, notif)
    
    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications."""
        notifications = self.get_notifications(user_id)
        return sum(1 for n in notifications if not n.get("read"))
    
    # Convenience methods for specific notification types
    
    async def notify_article_ready(self, user_id: str, article_id: str, title: str):
        """Notify user that new articles are available."""
        await self.send_notification(
            user_id=user_id,
            type=NotificationType.ARTICLE_READY,
            title="New Articles",
            message=f"New articles available including: {title[:50]}...",
            link=f"/articles/{article_id}"
        )
    
    async def notify_brief_ready(self, user_id: str, brief_id: str):
        """Notify user that daily brief is ready."""
        await self.send_notification(
            user_id=user_id,
            type=NotificationType.BRIEF_READY,
            title="Daily Brief Ready",
            message="Your personalized daily brief is ready to read.",
            priority=NotificationPriority.HIGH,
            link=f"/brief/{brief_id}"
        )
    
    async def notify_document_processed(self, user_id: str, document_id: str, title: str):
        """Notify user that document processing is complete."""
        await self.send_notification(
            user_id=user_id,
            type=NotificationType.DOCUMENT_PROCESSED,
            title="Document Ready",
            message=f"Your document '{title}' has been processed.",
            link=f"/library/{document_id}"
        )
    
    async def notify_scout_finding(self, user_id: str, scout_id: str, finding_title: str):
        """Notify user of new scout finding."""
        await self.send_notification(
            user_id=user_id,
            type=NotificationType.SCOUT_FINDING,
            title="New Finding",
            message=f"Your Scout found: {finding_title[:60]}...",
            link=f"/scout/{scout_id}/findings"
        )
    
    async def notify_budget_warning(self, user_id: str, used_percent: float):
        """Notify user when approaching budget limit."""
        await self.send_notification(
            user_id=user_id,
            type=NotificationType.BUDGET_WARNING,
            title="Budget Warning",
            message=f"You've used {used_percent:.0f}% of your monthly AI budget.",
            priority=NotificationPriority.HIGH,
            link="/settings/billing"
        )


# Singleton instance
notification_service = NotificationService()
