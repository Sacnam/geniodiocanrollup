"""
Database configuration and session management.

MIGRATION STRATEGY (DEV-001):
    This module provides two ways to initialize the database:
    
    1. Alembic Migrations (RECOMMENDED for production):
       Use `alembic upgrade head` to apply migrations.
       This is the preferred method for production deployments.
       
       $ cd backend
       $ alembic upgrade head
       
    2. init_db() (Development/Testing ONLY):
       Uses SQLModel.metadata.create_all() which creates tables
       but cannot alter existing schemas. Only suitable for
       fresh database instances.
    
    Migration files are located in: backend/alembic/versions/
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

from app.core.config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def init_db():
    """Initialize database tables.
    
    WARNING: This uses create_all() which cannot alter existing tables.
    For production, use Alembic migrations instead:
        $ alembic upgrade head
    
    This function is suitable for:
        - Development environments with fresh databases
        - Test fixtures that create temporary databases
        - Quick prototyping
    
    It is NOT suitable for:
        - Production deployments (use Alembic)
        - Databases with existing data (will not migrate)
    """
    # Import all models to register them with SQLModel
    from app.models import (
        Article,
        Brief,
        BriefSection,
        Document,
        DocumentChunk,
        DocumentCollection,
        DocumentCollectionLink,
        DocumentHighlight,
        Feed,
        PKGEdge,
        PKGNode,
        ScoutAgent,
        ScoutExecution,
        ScoutFinding,
        ScoutInsight,
        User,
        UserArticleContext,
        UserFeed,
    )
    
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session for dependency injection.
    
    Usage in FastAPI endpoints:
        @router.get("/items")
        def get_items(db: Session = Depends(get_session)):
            ...
    
    Yields:
        Session: SQLModel/SQLAlchemy session
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
