from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.database import check_db_connection, get_db_stats
from app.core.qdrant import qdrant_service
from app.core.redis import redis_client

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    services: dict


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    services = {
        "database": check_db_connection(),
        "redis": redis_client.ping(),
        "qdrant": False,
    }
    
    # Check Qdrant
    try:
        qdrant_service.connect()
        services["qdrant"] = True
    except Exception:
        pass
    
    all_healthy = all(services.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        services=services,
    )


@router.get("/health/stats")
async def health_stats():
    """Database statistics."""
    try:
        stats = get_db_stats()
        return {
            "status": "ok",
            "stats": stats,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@router.get("/")
async def root():
    return {
        "message": "Welcome to Genio API",
        "version": "1.0.0",
        "docs": "/docs",
    }
