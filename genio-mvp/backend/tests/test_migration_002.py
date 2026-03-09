"""Test migration 002 - Add library and lab tables."""
import pytest
from sqlalchemy import inspect


class TestMigration002:
    """Test that migration 002 creates all required tables."""

    def test_brief_sections_table_exists(self, db_engine):
        """Brief sections table should exist."""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        
        assert "brief_sections" in tables
        assert "brief_section_articles" in tables

    def test_document_tables_exist(self, db_engine):
        """All document-related tables should exist."""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        
        assert "documents" in tables
        assert "document_chunks" in tables
        assert "document_collections" in tables
        assert "document_collection_links" in tables
        assert "document_highlights" in tables

    def test_pkg_tables_exist(self, db_engine):
        """All PKG tables should exist."""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        
        assert "pkg_nodes" in tables
        assert "pkg_edges" in tables
        assert "pkg_extractions" in tables

    def test_scout_tables_exist(self, db_engine):
        """All scout tables should exist."""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        
        assert "scout_agents" in tables
        assert "scout_findings" in tables
        assert "scout_executions" in tables
        assert "scout_insights" in tables

    def test_ai_activity_logs_table_exists(self, db_engine):
        """AI activity logs table should exist."""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        
        assert "ai_activity_logs" in tables

    def test_ai_activity_logs_structure(self, db_engine):
        """AI activity logs should have correct columns."""
        inspector = inspect(db_engine)
        columns = {col['name'] for col in inspector.get_columns('ai_activity_logs')}
        
        expected = {
            'id', 'user_id', 'operation', 'model', 'input_tokens',
            'output_tokens', 'total_tokens', 'cost', 'resource_type',
            'resource_id', 'latency_ms', 'status', 'error_message',
            'cached', 'created_at'
        }
        
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_documents_table_structure(self, db_engine):
        """Documents table should have correct columns."""
        inspector = inspect(db_engine)
        columns = {col['name'] for col in inspector.get_columns('documents')}
        
        expected = {
            'id', 'user_id', 'filename', 'original_filename', 'file_path',
            'file_size_bytes', 'mime_type', 'doc_type', 'title', 'content',
            'excerpt', 'page_count', 'word_count', 'author', 'source_url',
            'tags', 'status', 'processing_state', 'processing_error',
            'retry_count', 'extracted_at', 'processed_at', 'state_changed_at',
            'embedding_vector_id', 'is_scanned', 'ocr_confidence',
            'created_at', 'updated_at'
        }
        
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_pkg_nodes_table_structure(self, db_engine):
        """PKG nodes table should have correct columns."""
        inspector = inspect(db_engine)
        columns = {col['name'] for col in inspector.get_columns('pkg_nodes')}
        
        expected = {
            'id', 'user_id', 'node_type', 'name', 'definition',
            'source_atoms', 'source_documents', 'confidence',
            'embedding_vector_id', 'knowledge_state', 'last_seen',
            'review_count', 'relationships', 'created_at', 'updated_at'
        }
        
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_scout_agents_table_structure(self, db_engine):
        """Scout agents table should have correct columns."""
        inspector = inspect(db_engine)
        columns = {col['name'] for col in inspector.get_columns('scout_agents')}
        
        expected = {
            'id', 'user_id', 'name', 'description', 'research_question',
            'keywords', 'exclude_keywords', 'sources', 'source_config',
            'min_relevance_score', 'content_types', 'date_range_days',
            'schedule', 'last_run_at', 'next_run_at', 'status', 'is_active',
            'total_findings', 'unread_findings', 'created_at', 'updated_at'
        }
        
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_foreign_keys_exist(self, db_engine):
        """Foreign key constraints should be in place."""
        inspector = inspect(db_engine)
        
        # Documents -> Users
        fks = inspector.get_foreign_keys('documents')
        fk_targets = {fk['referred_table'] for fk in fks}
        assert 'users' in fk_targets
        
        # Scout findings -> Scout agents
        fks = inspector.get_foreign_keys('scout_findings')
        fk_targets = {fk['referred_table'] for fk in fks}
        assert 'scout_agents' in fk_targets
        assert 'users' in fk_targets
        
        # PKG edges -> Users
        fks = inspector.get_foreign_keys('pkg_edges')
        fk_targets = {fk['referred_table'] for fk in fks}
        assert 'users' in fk_targets

    def test_indexes_exist(self, db_engine):
        """Important indexes should be created."""
        inspector = inspect(db_engine)
        
        # Documents indexes
        doc_indexes = {idx['name'] for idx in inspector.get_indexes('documents')}
        assert 'ix_documents_user_id' in doc_indexes
        assert 'ix_documents_status' in doc_indexes
        
        # Scout findings indexes
        finding_indexes = {idx['name'] for idx in inspector.get_indexes('scout_findings')}
        assert 'ix_scout_findings_scout_id' in finding_indexes
        assert 'ix_scout_findings_relevance_score' in finding_indexes
        assert 'ix_scout_findings_is_saved' in finding_indexes
