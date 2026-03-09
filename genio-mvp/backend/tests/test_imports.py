"""
Test that all imports work correctly.
This catches circular imports and missing modules.
"""
import pytest


class TestImports:
    """Test module imports."""

    def test_import_main(self):
        """Should import main app."""
        from app.main import app
        assert app is not None

    def test_import_models(self):
        """Should import all models."""
        from app.models import (
            User, Feed, Article, Brief, Document,
            PKGNode, PKGEdge, ScoutAgent, AIActivityLog
        )
        assert all([User, Feed, Article, Brief, Document])

    def test_import_api_routers(self):
        """Should import all API routers."""
        from app.api import (
            articles, auth, billing, briefs, documents, feeds,
            library_advanced, scouts
        )
        from app.api.v1 import admin, library, reading_list, webhooks
        assert all([articles, auth, billing, briefs, documents, feeds])

    def test_import_core_modules(self):
        """Should import core modules."""
        from app.core import (
            config, database, auth, redis, qdrant,
            ai_gateway
        )
        assert all([config, database, auth])

    def test_import_services(self):
        """Should import services."""
        from app.services import ai_service, document_service
        assert ai_service is not None
        assert document_service is not None

    def test_import_library_modules(self):
        """Should import library modules."""
        from app.library import (
            parsers, semantic_chunker, graph_rag,
            graph_extractor, embeddings, pkg_models
        )
        assert all([parsers, semantic_chunker, graph_rag])

    def test_import_lab_modules(self):
        """Should import lab modules."""
        from app.lab import models, engine, scout_advanced
        assert all([models, engine, scout_advanced])

    def test_import_tasks(self):
        """Should import Celery tasks."""
        from app.tasks import celery
        from app.tasks import (
            feed_tasks, article_tasks, brief_tasks,
            sweeper, webhook_tasks
        )
        assert celery.celery_app is not None

    def test_import_knowledge(self):
        """Should import knowledge modules."""
        from app.knowledge import vector_store
        assert vector_store is not None

    def test_import_api_deps(self):
        """Should import API dependencies."""
        from app.api.deps import (
            get_db, get_current_user, require_admin,
            get_pagination_params
        )
        assert all([get_db, get_current_user, require_admin])

    def test_no_circular_imports(self):
        """Should not have circular imports."""
        # Import everything in order
        import app.models
        import app.core
        import app.services
        import app.library
        import app.lab
        import app.api
        import app.tasks
        
        # If we get here without exception, no circular imports
        assert True
