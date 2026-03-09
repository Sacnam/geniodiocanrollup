"""Add comments system.

Revision ID: 014
Revises: 013
Create Date: 2026-02-18 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '014'
down_revision: Union[str, None] = '013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Comments table
    op.create_table(
        'comments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('article_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('parent_id', sa.String(), nullable=True),
        sa.Column('depth', sa.Integer(), default=0),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('content_html', sa.String(), nullable=True),
        sa.Column('mentions', sa.String(), default='[]'),
        sa.Column('likes_count', sa.Integer(), default=0),
        sa.Column('replies_count', sa.Integer(), default=0),
        sa.Column('is_edited', sa.Boolean(), default=False),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_by', sa.String(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), default=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes
    op.create_index('ix_comments_article_id', 'comments', ['article_id'])
    op.create_index('ix_comments_user_id', 'comments', ['user_id'])
    op.create_index('ix_comments_parent_id', 'comments', ['parent_id'])
    op.create_index('ix_comments_created_at', 'comments', ['created_at'])
    
    # Comment likes table
    op.create_table(
        'comment_likes',
        sa.Column('comment_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('comment_id', 'user_id')
    )
    
    op.create_index('ix_comment_likes_comment_id', 'comment_likes', ['comment_id'])
    op.create_index('ix_comment_likes_user_id', 'comment_likes', ['user_id'])


def downgrade() -> None:
    op.drop_table('comment_likes')
    op.drop_table('comments')
