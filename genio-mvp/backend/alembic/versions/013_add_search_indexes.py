"""Add search-related indexes and triggers.

Revision ID: 013
Revises: 012
Create Date: 2026-02-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add GIN index for article content search (as fallback)
    op.create_index(
        'ix_articles_content_gin',
        'articles',
        [sa.text("to_tsvector('english', content)")],
        postgresql_using='gin'
    )
    
    # Add GIN index for title search
    op.create_index(
        'ix_articles_title_gin',
        'articles',
        [sa.text("to_tsvector('english', title)")],
        postgresql_using='gin'
    )
    
    # Index on author for filtering
    op.create_index('ix_articles_author', 'articles', ['author'])
    
    # Composite index for common queries
    op.create_index(
        'ix_user_article_context_user_read',
        'user_article_context',
        ['user_id', 'is_read', 'updated_at']
    )


def downgrade() -> None:
    op.drop_index('ix_articles_content_gin', table_name='articles')
    op.drop_index('ix_articles_title_gin', table_name='articles')
    op.drop_index('ix_articles_author', table_name='articles')
    op.drop_index('ix_user_article_context_user_read', table_name='user_article_context')
