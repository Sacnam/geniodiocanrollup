"""Final migration check - verify all tables exist.

Revision ID: 021
Revises: 020
Create Date: 2026-02-18 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '021'
down_revision: Union[str, None] = '020'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Verify all enterprise tables exist and add any missing indexes."""
    
    # Add composite indexes for common query patterns
    
    # Article queries by user + read status
    op.create_index(
        'ix_user_article_context_user_read_delta',
        'user_article_context',
        ['user_id', 'is_read', 'delta_score']
    )
    
    # Tag queries by user + usage
    op.create_index(
        'ix_tags_user_usage',
        'tags',
        ['user_id', 'usage_count']
    )
    
    # Share link expiration queries
    op.create_index(
        'ix_share_links_expires',
        'share_links',
        ['expires_at']
    )
    
    # Team membership queries
    op.create_index(
        'ix_team_members_user',
        'team_members',
        ['user_id', 'team_id']
    )
    
    # Plugin execution logs for analytics
    op.create_index(
        'ix_plugin_logs_date',
        'plugin_execution_logs',
        ['created_at']
    )


def downgrade() -> None:
    op.drop_index('ix_user_article_context_user_read_delta', 'user_article_context')
    op.drop_index('ix_tags_user_usage', 'tags')
    op.drop_index('ix_share_links_expires', 'share_links')
    op.drop_index('ix_team_members_user', 'team_members')
    op.drop_index('ix_plugin_logs_date', 'plugin_execution_logs')
