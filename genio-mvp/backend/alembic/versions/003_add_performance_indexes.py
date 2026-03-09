"""Add performance indexes

Revision ID: 003
Revises: 002
Create Date: 2026-02-18 11:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================
    # ARTICLES - Performance indexes
    # ==========================================
    # Composite index for fetching ready articles by date
    op.create_index(
        'ix_articles_status_created',
        'articles',
        ['processing_status', 'created_at'],
        postgresql_using='btree'
    )
    
    # Index for feed fetching
    op.create_index(
        'ix_articles_feed_created',
        'articles',
        ['feed_id', 'created_at'],
        postgresql_using='btree'
    )
    
    # ==========================================
    # USER ARTICLE CONTEXT - Performance indexes
    # ==========================================
    # Composite index for user feed with pagination
    op.create_index(
        'ix_context_user_created',
        'user_article_context',
        ['user_id', 'created_at'],
        postgresql_using='btree'
    )
    
    # Index for delta score queries
    op.create_index(
        'ix_context_user_delta',
        'user_article_context',
        ['user_id', 'delta_score'],
        postgresql_using='btree'
    )
    
    # Composite index for unread articles
    op.create_index(
        'ix_context_user_unread',
        'user_article_context',
        ['user_id', 'is_read', 'created_at'],
        postgresql_using='btree'
    )
    
    # ==========================================
    # SCOUT FINDINGS - Performance indexes
    # ==========================================
    # Composite index for filtering findings
    op.create_index(
        'ix_scout_findings_scout_read_score',
        'scout_findings',
        ['scout_id', 'is_read', 'relevance_score'],
        postgresql_using='btree'
    )
    
    # Index for user findings
    op.create_index(
        'ix_scout_findings_user_created',
        'scout_findings',
        ['user_id', 'created_at'],
        postgresql_using='btree'
    )
    
    # ==========================================
    # BRIEFS - Performance indexes
    # ==========================================
    # Composite index for today's brief query
    op.create_index(
        'ix_briefs_user_date',
        'briefs',
        ['user_id', 'scheduled_for'],
        postgresql_using='btree'
    )
    
    # ==========================================
    # AI ACTIVITY LOGS - Performance indexes
    # ==========================================
    # Composite index for cost aggregation queries
    op.create_index(
        'ix_ai_logs_user_created',
        'ai_activity_logs',
        ['user_id', 'created_at'],
        postgresql_using='btree'
    )
    
    # Index for operation analysis
    op.create_index(
        'ix_ai_logs_operation_created',
        'ai_activity_logs',
        ['operation', 'created_at'],
        postgresql_using='btree'
    )
    
    # ==========================================
    # DOCUMENTS - Performance indexes
    # ==========================================
    # Composite index for user documents by status
    op.create_index(
        'ix_documents_user_status',
        'documents',
        ['user_id', 'status', 'created_at'],
        postgresql_using='btree'
    )
    
    # ==========================================
    # FULL TEXT SEARCH (optional - GIN indexes)
    # ==========================================
    # GIN index for article search (if using PostgreSQL full-text)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_articles_search 
        ON articles USING GIN(
            to_tsvector('english', 
                coalesce(title, '') || ' ' || 
                coalesce(content, '')
            )
        )
    """)
    
    # GIN index for document search
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_documents_search 
        ON documents USING GIN(
            to_tsvector('english', 
                coalesce(title, '') || ' ' || 
                coalesce(content, '')
            )
        )
    """)


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index('ix_documents_search', table_name='documents')
    op.drop_index('ix_articles_search', table_name='articles')
    op.drop_index('ix_documents_user_status', table_name='documents')
    op.drop_index('ix_ai_logs_operation_created', table_name='ai_activity_logs')
    op.drop_index('ix_ai_logs_user_created', table_name='ai_activity_logs')
    op.drop_index('ix_briefs_user_date', table_name='briefs')
    op.drop_index('ix_scout_findings_user_created', table_name='scout_findings')
    op.drop_index('ix_scout_findings_scout_read_score', table_name='scout_findings')
    op.drop_index('ix_context_user_unread', table_name='user_article_context')
    op.drop_index('ix_context_user_delta', table_name='user_article_context')
    op.drop_index('ix_context_user_created', table_name='user_article_context')
    op.drop_index('ix_articles_feed_created', table_name='articles')
    op.drop_index('ix_articles_status_created', table_name='articles')
