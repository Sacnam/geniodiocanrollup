"""
Observability setup for Datadog (T059 / B08).
Implements 5 SLIs with metrics and alerting.
"""
import functools
import time
from typing import Callable, Optional

from app.core.config import settings


class MetricsCollector:
    """
    Collects metrics for SLI monitoring.
    B08: 5 SLIs + alerting.
    """
    
    # SLI Definitions
    SLIS = {
        "feed_fetch_success_rate": {
            "target": 0.98,
            "alert_threshold": 0.95,
            "description": "Percentage of successful feed fetches",
        },
        "extraction_success_rate": {
            "target": 0.95,
            "alert_threshold": 0.90,
            "description": "Percentage of successful article extractions",
        },
        "embedding_generation_p95": {
            "target": 2.0,  # seconds
            "alert_threshold": 5.0,
            "description": "P95 latency for embedding generation",
        },
        "brief_delivery_success_rate": {
            "target": 0.99,
            "alert_threshold": 0.95,
            "description": "Percentage of successful brief deliveries",
        },
        "ai_budget_utilization": {
            "target": 0.80,
            "alert_threshold": 0.90,
            "description": "Percentage of AI budget utilized",
        },
    }
    
    def __init__(self):
        self.metrics = {}
        self.counters = {}
        self.timers = {}
    
    def increment(self, metric_name: str, tags: Optional[dict] = None, value: int = 1):
        """Increment a counter metric."""
        key = self._make_key(metric_name, tags)
        if key not in self.counters:
            self.counters[key] = 0
        self.counters[key] += value
    
    def gauge(self, metric_name: str, value: float, tags: Optional[dict] = None):
        """Record a gauge metric."""
        key = self._make_key(metric_name, tags)
        self.metrics[key] = value
    
    def timer(self, metric_name: str, duration_ms: float, tags: Optional[dict] = None):
        """Record a timer metric."""
        key = self._make_key(metric_name, tags)
        if key not in self.timers:
            self.timers[key] = []
        self.timers[key].append(duration_ms)
    
    def histogram(self, metric_name: str, value: float, tags: Optional[dict] = None):
        """Record a histogram value."""
        key = self._make_key(metric_name, tags)
        if key not in self.metrics:
            self.metrics[key] = []
        if isinstance(self.metrics[key], list):
            self.metrics[key].append(value)
    
    def _make_key(self, name: str, tags: Optional[dict]) -> str:
        """Create metric key with tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}:{v}" for k, v in sorted(tags.items()))
        return f"{name}|{tag_str}"
    
    def get_sli_status(self) -> dict:
        """Get current SLI status for all metrics."""
        status = {}
        
        for sli_name, config in self.SLIS.items():
            # Calculate current value based on metric type
            if "success_rate" in sli_name:
                current = self._calculate_success_rate(sli_name)
            elif "p95" in sli_name:
                current = self._calculate_p95(sli_name)
            elif "budget" in sli_name:
                current = self.metrics.get(sli_name, 0)
            else:
                current = self.metrics.get(sli_name, 0)
            
            status[sli_name] = {
                "current": current,
                "target": config["target"],
                "alert_threshold": config["alert_threshold"],
                "status": "healthy" if self._is_healthy(sli_name, current) else "alert",
                "description": config["description"],
            }
        
        return status
    
    def _calculate_success_rate(self, prefix: str) -> float:
        """Calculate success rate from success/total counters."""
        success = self.counters.get(f"{prefix}.success", 0)
        total = self.counters.get(f"{prefix}.total", 0)
        return success / total if total > 0 else 1.0
    
    def _calculate_p95(self, metric_name: str) -> float:
        """Calculate P95 from timer values."""
        key = self._make_key(metric_name, None)
        values = self.timers.get(key, [])
        if not values:
            return 0.0
        sorted_values = sorted(values)
        idx = int(len(sorted_values) * 0.95)
        return sorted_values[min(idx, len(sorted_values) - 1)]
    
    def _is_healthy(self, sli_name: str, current: float) -> bool:
        """Check if SLI is within healthy threshold."""
        config = self.SLIS[sli_name]
        threshold = config["alert_threshold"]
        
        # For latency/budget, lower is better
        if "p95" in sli_name or "budget" in sli_name:
            return current <= threshold
        # For success rates, higher is better
        return current >= threshold


# Global metrics collector
metrics = MetricsCollector()


def timed(metric_name: str, tags: Optional[dict] = None):
    """Decorator to time function execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                metrics.increment(f"{metric_name}.success")
                return result
            except Exception:
                metrics.increment(f"{metric_name}.error")
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                metrics.timer(metric_name, duration_ms, tags)
        return wrapper
    return decorator


def counted(metric_name: str, tags: Optional[dict] = None):
    """Decorator to count function calls."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            metrics.increment(metric_name, tags)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Health check endpoint data
def get_health_metrics() -> dict:
    """Get health metrics for monitoring endpoint."""
    sli_status = metrics.get_sli_status()
    
    # Overall health
    all_healthy = all(s["status"] == "healthy" for s in sli_status.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "slis": sli_status,
        "counters": dict(metrics.counters),
    }
