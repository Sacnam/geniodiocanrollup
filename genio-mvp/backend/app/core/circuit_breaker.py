"""
Circuit Breaker pattern implementation (B05).
Prevents cascade failures when external APIs are down.
"""
import time
from enum import Enum
from functools import wraps
from typing import Callable, Optional


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for external API calls.
    
    - CLOSED: Normal operation, requests pass through
    - OPEN: After failure_threshold failures, reject requests
    - HALF_OPEN: After recovery_timeout, allow one test request
    
    B05: Circuit breaker pattern for resilience.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        fallback: Optional[Callable] = None
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.fallback = fallback
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.failure_count = 0
            else:
                # Circuit is open, use fallback or raise
                if self.fallback:
                    return self.fallback(*args, **kwargs)
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            if self.fallback:
                return self.fallback(*args, **kwargs)
            raise
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 3:
                # Service recovered, close circuit
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator support."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Global circuit breakers for external services
circuit_breakers = {
    "openai": CircuitBreaker(
        name="openai",
        failure_threshold=5,
        recovery_timeout=60,
    ),
    "gemini": CircuitBreaker(
        name="gemini",
        failure_threshold=5,
        recovery_timeout=60,
    ),
    "sendgrid": CircuitBreaker(
        name="sendgrid",
        failure_threshold=5,
        recovery_timeout=120,
    ),
}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Get a circuit breaker by name."""
    return circuit_breakers.get(name)
