"""Add saved views and filters.

Revision ID: 012
Revises: 011
Create Date: 2026-02-18 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'saved_views',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('filters', sa.String(), default='{}'),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('is_pinned', sa.Boolean(), default=False),
        sa.Column('position', sa.Integer(), default=0),
        sa.Column('share_token', sa.String(), nullable=True),
        sa.Column('share_enabled', sa.Boolean(), default=False),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('use_count', sa.Integer(), default=0),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes
    op.create_index('ix_saved_views_user_id', 'saved_views', ['user_id'])
    op.create_index('ix_saved_views_share_token', 'saved_views', ['share_token'])


def downgrade() -> None:
    op.drop_table('saved_views')
