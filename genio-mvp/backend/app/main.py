"""
Genio Knowledge OS - Stream MVP
FastAPI main application.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api import articles, auth, billing, briefs, documents, feeds, library_advanced, scouts, notifications, tags, saved_views, search, comments, keyboard_shortcuts, analytics, brief_templates, sharing, two_factor, plugins
from app.api.v1 import admin, reading_list, library, webhooks
from app.api.auth_password_reset import router as auth_password_reset_router
from app.realtime import websocket
from app.core.config import settings
from app.core.database import init_db
from app.core.observability import get_health_metrics
from app.core.openapi import custom_openapi
from app.core.rate_limit import RateLimitMiddleware
from app.core.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    init_db()
    yield
    # Shutdown


app = FastAPI(
    title="Genio Knowledge OS",
    description="Intelligent feed aggregator with AI-powered daily briefs",
    version="2.1.0",
    lifespan=lifespan,
)

# Security Headers Middleware (must be first)
app.add_middleware(SecurityHeadersMiddleware)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# CORS - Restrictive configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept", "Origin"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=600,
)


# Override OpenAPI
app.openapi = lambda: custom_openapi(app)


# Health check
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "service": "genio-api"
    }


@app.get("/metrics")
def metrics_endpoint():
    """Metrics endpoint for monitoring (T059 / B08)."""
    return get_health_metrics()


@app.get("/openapi.json")
def openapi_json():
    """Export OpenAPI schema as JSON."""
    return custom_openapi(app)


# API routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(auth_password_reset_router, prefix="/api/v1")
app.include_router(feeds.router, prefix="/api/v1")
app.include_router(articles.router, prefix="/api/v1")
app.include_router(briefs.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(scouts.router, prefix="/api/v1")
app.include_router(library_advanced.router, prefix="/api/v1")
app.include_router(reading_list.router, prefix="/api/v1/reading-list")
app.include_router(library.router, prefix="/api/v1/library")
app.include_router(admin.router, prefix="/api/v1/admin")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1/webhooks")
app.include_router(websocket.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1/tags")
app.include_router(saved_views.router, prefix="/api/v1/views")
app.include_router(search.router, prefix="/api/v1/search")
app.include_router(comments.router, prefix="/api/v1")
app.include_router(keyboard_shortcuts.router, prefix="/api/v1/shortcuts")
app.include_router(analytics.router, prefix="/api/v1/analytics")
app.include_router(brief_templates.router, prefix="/api/v1/brief-templates")
app.include_router(sharing.router, prefix="/api/v1")
app.include_router(two_factor.router, prefix="/api/v1")
app.include_router(plugins.router, prefix="/api/v1/plugins")


# Error handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
