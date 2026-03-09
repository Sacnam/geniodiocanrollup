"""
Distributed Tracing with OpenTelemetry
"""
import functools
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode

from app.core.config import settings


# Global tracer provider
_tracer_provider: Optional[TracerProvider] = None
_tracer: Optional[trace.Tracer] = None


def setup_tracing(app_name: str = "genio-api", app_version: str = "1.0.0"):
    """Initialize OpenTelemetry tracing."""
    global _tracer_provider, _tracer
    
    # Create resource
    resource = Resource.create({
        SERVICE_NAME: app_name,
        SERVICE_VERSION: app_version,
        "deployment.environment": settings.ENVIRONMENT,
    })
    
    # Create provider
    _tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(_tracer_provider)
    
    # Configure exporters
    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        # OTLP exporter for production (Datadog, Jaeger, etc.)
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            headers=settings.OTEL_EXPORTER_OTLP_HEADERS,
        )
        _tracer_provider.add_span_processor(
            BatchSpanProcessor(otlp_exporter)
        )
    else:
        # Console exporter for development
        console_exporter = ConsoleSpanExporter()
        _tracer_provider.add_span_processor(
            BatchSpanProcessor(console_exporter)
        )
    
    # Get tracer
    _tracer = trace.get_tracer(app_name, app_version)
    
    # Auto-instrument libraries
    RedisInstrumentor().instrument()
    
    return _tracer_provider


def instrument_fastapi(app):
    """Instrument FastAPI application."""
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="/health,/metrics",  # Exclude health checks
    )


def instrument_sqlalchemy(engine):
    """Instrument SQLAlchemy."""
    SQLAlchemyInstrumentor().instrument(
        engine=engine,
    )


def get_tracer() -> trace.Tracer:
    """Get the global tracer."""
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer("genio-api")
    return _tracer


@contextmanager
def span(name: str, kind: trace.SpanKind = trace.SpanKind.INTERNAL,
         attributes: Optional[Dict[str, Any]] = None):
    """Context manager for creating spans."""
    tracer = get_tracer()
    with tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def trace_function(name: Optional[str] = None, 
                   attributes: Optional[Dict[str, Any]] = None):
    """Decorator to trace function execution."""
    def decorator(func: Callable):
        span_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(span_name) as span:
                # Add function attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.success", True)
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    span.set_attribute("function.success", False)
                    raise
        
        # Handle async functions
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                tracer = get_tracer()
                with tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_attribute("function.success", True)
                        return result
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        span.set_attribute("function.success", False)
                        raise
            return async_wrapper
        
        return wrapper
    return decorator


class TracedSpan:
    """Helper class for manual span management."""
    
    def __init__(self, name: str, kind: trace.SpanKind = trace.SpanKind.INTERNAL):
        self.name = name
        self.kind = kind
        self.span = None
        self.tracer = get_tracer()
    
    def __enter__(self):
        self.span = self.tracer.start_span(self.name, kind=self.kind)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
            self.span.record_exception(exc_val)
        self.span.end()
    
    def set_attribute(self, key: str, value: Any):
        """Set span attribute."""
        self.span.set_attribute(key, value)
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add event to span."""
        self.span.add_event(name, attributes or {})
    
    def record_exception(self, exception: Exception):
        """Record exception in span."""
        self.span.record_exception(exception)


# Celery task tracing
def trace_celery_task(task_name: str):
    """Decorator to trace Celery tasks."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(
                f"celery.task.{task_name}",
                kind=trace.SpanKind.CONSUMER
            ) as span:
                span.set_attribute("celery.task_name", task_name)
                span.set_attribute("celery.args", str(args))
                span.set_attribute("celery.kwargs", str(kwargs))
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("celery.success", True)
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    span.set_attribute("celery.success", False)
                    raise
        return wrapper
    return decorator


# Database query tracing
def trace_db_query(operation: str, table: str):
    """Context manager for database operations."""
    return span(
        f"db.{operation}",
        kind=trace.SpanKind.CLIENT,
        attributes={
            "db.system": "postgresql",
            "db.operation": operation,
            "db.table": table,
        }
    )


# AI model call tracing
def trace_ai_call(model: str, operation: str):
    """Context manager for AI model calls."""
    return span(
        f"ai.{model}.{operation}",
        kind=trace.SpanKind.CLIENT,
        attributes={
            "ai.model": model,
            "ai.operation": operation,
        }
    )


# Cache operation tracing
def trace_cache(operation: str, cache_type: str = "redis"):
    """Context manager for cache operations."""
    return span(
        f"cache.{operation}",
        kind=trace.SpanKind.CLIENT,
        attributes={
            "cache.system": cache_type,
            "cache.operation": operation,
        }
    )


import asyncio  # noqa: E402
