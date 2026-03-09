"""Initial schema with indexes for performance.

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users table
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('tier', sa.String(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('monthly_ai_budget', sa.Float(), nullable=False),
        sa.Column('ai_budget_used_this_month', sa.Float(), nullable=False),
        sa.Column('budget_resets_at', sa.DateTime(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=False),
        sa.Column('brief_preferred_time', sa.String(), nullable=False),
        sa.Column('email_delivery_enabled', sa.Boolean(), nullable=False),
        sa.Column('google_oauth_id', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # User indexes
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_google_oauth_id', 'users', ['google_oauth_id'], unique=False)
    op.create_index('ix_users_created_at', 'users', ['created_at'], unique=False)
    
    # Feeds table
    op.create_table('feeds',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('last_fetched_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.String(), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=False),
        sa.Column('fetch_interval_minutes', sa.Integer(), nullable=False),
        sa.Column('avg_update_interval_minutes', sa.Integer(), nullable=True),
        sa.Column('etag', sa.String(), nullable=True),
        sa.Column('last_modified', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Feed indexes (T068)
    op.create_index('ix_feeds_user_id', 'feeds', ['user_id'], unique=False)
    op.create_index('ix_feeds_user_id_status', 'feeds', ['user_id', 'status'], unique=False)
    op.create_index('ix_feeds_last_fetched_at', 'feeds', ['last_fetched_at'], unique=False)
    op.create_index('ix_feeds_status_fetch_interval', 'feeds', ['status', 'fetch_interval_minutes'], unique=False)
    
    # Articles table
    op.create_table('articles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('source_feed_id', sa.String(), nullable=True),
        sa.Column('source_feed_title', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('excerpt', sa.String(), nullable=True),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('content_hash', sa.String(), nullable=False),
        sa.Column('global_summary', sa.Text(), nullable=True),
        sa.Column('summary_generated_at', sa.DateTime(), nullable=True),
        sa.Column('embedding_vector_id', sa.String(), nullable=True),
        sa.Column('processing_status', sa.String(), nullable=False),
        sa.Column('processing_started_at', sa.DateTime(), nullable=True),
        sa.Column('processing_attempts', sa.Integer(), nullable=False),
        sa.Column('processing_error', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['source_feed_id'], ['feeds.id'], ondelete='SET NULL')
    )
    
    # Article indexes (T068)
    op.create_index('ix_articles_url', 'articles', ['url'], unique=False)
    op.create_index('ix_articles_content_hash', 'articles', ['content_hash'], unique=False)
    op.create_index('ix_articles_embedding_vector_id', 'articles', ['embedding_vector_id'], unique=False)
    op.create_index('ix_articles_processing_status', 'articles', ['processing_status'], unique=False)
    op.create_index('ix_articles_created_at', 'articles', ['created_at'], unique=False)
    op.create_index('ix_articles_source_feed_id_created_at', 'articles', ['source_feed_id', 'created_at'], unique=False)
    
    # UserArticleContext table
    op.create_table('user_article_context',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('article_id', sa.String(), nullable=False),
        sa.Column('delta_score', sa.Float(), nullable=False),
        sa.Column('cluster_id', sa.String(), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=False),
        sa.Column('is_favorited', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'article_id', name='uq_user_article')
    )
    
    # Context indexes (T068)
    op.create_index('ix_context_user_id', 'user_article_context', ['user_id'], unique=False)
    op.create_index('ix_context_article_id', 'user_article_context', ['article_id'], unique=False)
    op.create_index('ix_context_user_delta', 'user_article_context', ['user_id', 'delta_score'], unique=False)
    op.create_index('ix_context_user_read', 'user_article_context', ['user_id', 'is_read', 'is_archived'], unique=False)
    op.create_index('ix_context_user_duplicate', 'user_article_context', ['user_id', 'is_duplicate'], unique=False)
    
    # Briefs table
    op.create_table('briefs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(), nullable=False),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('delivery_status', sa.String(), nullable=False),
        sa.Column('is_quiet_day', sa.Boolean(), nullable=False),
        sa.Column('quiet_day_reason', sa.String(), nullable=True),
        sa.Column('article_count', sa.Integer(), nullable=False),
        sa.Column('sources_cited', sa.JSON(), nullable=True),
        sa.Column('generation_cost_usd', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Brief indexes
    op.create_index('ix_briefs_user_id', 'briefs', ['user_id'], unique=False)
    op.create_index('ix_briefs_user_scheduled', 'briefs', ['user_id', 'scheduled_for'], unique=False)
    op.create_index('ix_briefs_scheduled_for', 'briefs', ['scheduled_for'], unique=False)


def downgrade():
    op.drop_table('briefs')
    op.drop_table('user_article_context')
    op.drop_table('articles')
    op.drop_table('feeds')
    op.drop_table('users')
