"""Add library and lab tables

Revision ID: 002
Revises: 001
Create Date: 2026-02-18 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================
    # BRIEF MODULE - Missing brief_sections
    # ==========================================
    op.create_table(
        'brief_sections',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('brief_id', sa.String(), nullable=False),
        sa.Column('section_type', sa.String(), nullable=False),  # executive_summary, key_stories, the_diff, emerging_trends
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['brief_id'], ['briefs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_brief_sections_brief_id', 'brief_sections', ['brief_id'])

    # Tabella intermedia per relationship BriefSection <-> Article
    op.create_table(
        'brief_section_articles',
        sa.Column('brief_section_id', sa.String(), nullable=False),
        sa.Column('article_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['brief_section_id'], ['brief_sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('brief_section_id', 'article_id')
    )

    # ==========================================
    # LIBRARY MODULE - Documents
    # ==========================================
    op.create_table(
        'documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=False),
        sa.Column('doc_type', sa.String(), nullable=False),  # pdf, text, markdown, html, epub
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('excerpt', sa.String(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),  # pending, uploaded, processing, etc.
        sa.Column('processing_state', sa.String(), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('extracted_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('state_changed_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('embedding_vector_id', sa.String(), nullable=True),
        sa.Column('is_scanned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ocr_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])
    op.create_index('ix_documents_embedding_vector_id', 'documents', ['embedding_vector_id'])
    op.create_index('ix_documents_status', 'documents', ['status'])

    # Document Chunks
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('embedding_vector_id', sa.String(), nullable=True),
        sa.Column('char_start', sa.Integer(), nullable=False),
        sa.Column('char_end', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('ix_document_chunks_embedding_vector_id', 'document_chunks', ['embedding_vector_id'])

    # Document Collections (folders)
    op.create_table(
        'document_collections',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('parent_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['document_collections.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_collections_user_id', 'document_collections', ['user_id'])
    op.create_index('ix_document_collections_parent_id', 'document_collections', ['parent_id'])

    # Document-Collection Links (many-to-many)
    op.create_table(
        'document_collection_links',
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('collection_id', sa.String(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['collection_id'], ['document_collections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('document_id', 'collection_id')
    )

    # Document Highlights (annotations)
    op.create_table(
        'document_highlights',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('char_start', sa.Integer(), nullable=False),
        sa.Column('char_end', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('highlighted_text', sa.Text(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('color', sa.String(), nullable=False, server_default='yellow'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_highlights_document_id', 'document_highlights', ['document_id'])
    op.create_index('ix_document_highlights_user_id', 'document_highlights', ['user_id'])

    # ==========================================
    # LIBRARY MODULE - PKG (Knowledge Graph)
    # ==========================================
    op.create_table(
        'pkg_nodes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('node_type', sa.String(), nullable=False),  # concept, atom, document
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('definition', sa.Text(), nullable=True),
        sa.Column('source_atoms', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('source_documents', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.8'),
        sa.Column('embedding_vector_id', sa.String(), nullable=True),
        sa.Column('knowledge_state', sa.String(), nullable=False, server_default='gap'),  # known, gap, learning
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('review_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('relationships', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pkg_nodes_user_id', 'pkg_nodes', ['user_id'])
    op.create_index('ix_pkg_nodes_node_type', 'pkg_nodes', ['node_type'])
    op.create_index('ix_pkg_nodes_embedding_vector_id', 'pkg_nodes', ['embedding_vector_id'])
    op.create_index('ix_pkg_nodes_knowledge_state', 'pkg_nodes', ['knowledge_state'])

    # PKG Edges
    op.create_table(
        'pkg_edges',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=False),
        sa.Column('edge_type', sa.String(), nullable=False),  # depends_on, supports, contradicts, etc.
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.8'),
        sa.Column('evidence_atoms', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pkg_edges_user_id', 'pkg_edges', ['user_id'])
    op.create_index('ix_pkg_edges_source_id', 'pkg_edges', ['source_id'])
    op.create_index('ix_pkg_edges_target_id', 'pkg_edges', ['target_id'])
    op.create_index('ix_pkg_edges_edge_type', 'pkg_edges', ['edge_type'])

    # PKG Extractions (log)
    op.create_table(
        'pkg_extractions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='running'),
        sa.Column('atoms_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('nodes_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('nodes_merged', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('edges_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pkg_extractions_user_id', 'pkg_extractions', ['user_id'])
    op.create_index('ix_pkg_extractions_document_id', 'pkg_extractions', ['document_id'])
    op.create_index('ix_pkg_extractions_status', 'pkg_extractions', ['status'])

    # ==========================================
    # LAB MODULE - Scout Agents
    # ==========================================
    op.create_table(
        'scout_agents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('research_question', sa.String(), nullable=False),
        sa.Column('keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('exclude_keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('sources', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='["feeds"]'),
        sa.Column('source_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('min_relevance_score', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('content_types', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='["article", "paper"]'),
        sa.Column('date_range_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('schedule', sa.String(), nullable=False, server_default='daily'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='idle'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('total_findings', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unread_findings', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scout_agents_user_id', 'scout_agents', ['user_id'])
    op.create_index('ix_scout_agents_status', 'scout_agents', ['status'])
    op.create_index('ix_scout_agents_is_active', 'scout_agents', ['is_active'])
    op.create_index('ix_scout_agents_next_run_at', 'scout_agents', ['next_run_at'])

    # Scout Findings
    op.create_table(
        'scout_findings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('scout_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),  # article, document, web_page
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=False),
        sa.Column('source_title', sa.String(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('matched_keywords', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('key_insights', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('contradictions', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_saved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_dismissed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['scout_id'], ['scout_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scout_findings_scout_id', 'scout_findings', ['scout_id'])
    op.create_index('ix_scout_findings_user_id', 'scout_findings', ['user_id'])
    op.create_index('ix_scout_findings_source_type', 'scout_findings', ['source_type'])
    op.create_index('ix_scout_findings_relevance_score', 'scout_findings', ['relevance_score'])
    op.create_index('ix_scout_findings_is_read', 'scout_findings', ['is_read'])
    op.create_index('ix_scout_findings_is_saved', 'scout_findings', ['is_saved'])
    op.create_index('ix_scout_findings_created_at', 'scout_findings', ['created_at'])

    # Scout Executions (log)
    op.create_table(
        'scout_executions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('scout_id', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='running'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sources_checked', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('items_scanned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('findings_generated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('ai_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.ForeignKeyConstraint(['scout_id'], ['scout_agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scout_executions_scout_id', 'scout_executions', ['scout_id'])
    op.create_index('ix_scout_executions_status', 'scout_executions', ['status'])

    # Scout Insights
    op.create_table(
        'scout_insights',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('scout_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('insight_type', sa.String(), nullable=False),  # trend, pattern, gap, opportunity
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('supporting_findings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['scout_id'], ['scout_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scout_insights_scout_id', 'scout_insights', ['scout_id'])
    op.create_index('ix_scout_insights_user_id', 'scout_insights', ['user_id'])
    op.create_index('ix_scout_insights_insight_type', 'scout_insights', ['insight_type'])


    # ==========================================
    # ACTIVITY LOG - AI Cost tracking
    # ==========================================
    op.create_table(
        'ai_activity_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('operation', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='success'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('cached', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ai_activity_logs_user_id', 'ai_activity_logs', ['user_id'])
    op.create_index('ix_ai_activity_logs_created_at', 'ai_activity_logs', ['created_at'])
    op.create_index('ix_ai_activity_logs_operation', 'ai_activity_logs', ['operation'])


def downgrade() -> None:
    # Drop in reverse order to handle dependencies
    
    # Activity logs
    op.drop_table('ai_activity_logs')
    
    # Lab tables
    op.drop_table('scout_insights')
    op.drop_table('scout_executions')
    op.drop_table('scout_findings')
    op.drop_table('scout_agents')
    
    # PKG tables
    op.drop_table('pkg_extractions')
    op.drop_table('pkg_edges')
    op.drop_table('pkg_nodes')
    
    # Document tables
    op.drop_table('document_highlights')
    op.drop_table('document_collection_links')
    op.drop_table('document_collections')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    
    # Brief tables
    op.drop_table('brief_section_articles')
    op.drop_table('brief_sections')
