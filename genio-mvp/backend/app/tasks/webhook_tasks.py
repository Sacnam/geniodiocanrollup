"""
Webhook Delivery Tasks
"""
import json
from datetime import datetime

import httpx

from app.tasks.celery import celery_app
from app.core.observability import MetricsManager
from app.core.tracing import trace_celery_task

metrics = MetricsManager()


@celery_app.task(bind=True, max_retries=5)
@trace_celery_task("webhook.deliver")
def deliver_webhook(self, webhook_id: str, delivery_id: str, url: str,
                    payload: dict, secret: str = None):
    """
    Deliver webhook to endpoint.
    
    Args:
        webhook_id: Webhook ID
        delivery_id: Unique delivery ID
        url: Target URL
        payload: Event payload
        secret: HMAC secret for signing
    """
    from app.api.v1.webhooks import get_webhook_manager
    
    manager = get_webhook_manager()
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Genio-Webhook/1.0",
        "X-Webhook-ID": webhook_id,
        "X-Delivery-ID": delivery_id,
        "X-Event-Type": payload.get("event"),
    }
    
    # Add signature if secret provided
    if secret:
        signature = manager.generate_signature(payload, secret)
        headers["X-Webhook-Signature"] = signature
    
    try:
        # Deliver with timeout
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
        
        # Success
        metrics.increment("webhook.delivered", tags={"status": "success"})
        
        return {
            "delivery_id": delivery_id,
            "status": "delivered",
            "response_status": response.status_code,
            "delivered_at": datetime.utcnow().isoformat(),
        }
    
    except httpx.TimeoutException:
        # Retry with backoff
        metrics.increment("webhook.delivered", tags={"status": "timeout"})
        raise self.retry(countdown=self._get_retry_delay(self.request.retries))
    
    except httpx.HTTPStatusError as e:
        # Retry on 5xx, fail on 4xx
        if e.response.status_code >= 500:
            metrics.increment("webhook.delivered", 
                            tags={"status": f"error_{e.response.status_code}"})
            raise self.retry(countdown=self._get_retry_delay(self.request.retries))
        else:
            # 4xx errors - don't retry
            metrics.increment("webhook.delivered", 
                            tags={"status": f"fail_{e.response.status_code}"})
            return {
                "delivery_id": delivery_id,
                "status": "failed",
                "error": f"HTTP {e.response.status_code}",
                "response_body": e.response.text,
            }
    
    except Exception as e:
        metrics.increment("webhook.delivered", tags={"status": "exception"})
        raise self.retry(countdown=self._get_retry_delay(self.request.retries), 
                        exc=e)


def _get_retry_delay(retry_count: int) -> int:
    """Get delay for retry attempt."""
    delays = [5, 30, 300, 1800, 3600]  # 5s, 30s, 5min, 30min, 1hour
    return delays[min(retry_count, len(delays) - 1)]
