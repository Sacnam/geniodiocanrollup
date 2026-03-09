"""Add analytics snapshots table.

Revision ID: 016
Revises: 015
Create Date: 2026-02-18 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '016'
down_revision: Union[str, None] = '015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'analytics_snapshots',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('articles_read', sa.Integer(), default=0),
        sa.Column('articles_archived', sa.Integer(), default=0),
        sa.Column('articles_favorited', sa.Integer(), default=0),
        sa.Column('total_reading_time_minutes', sa.Integer(), default=0),
        sa.Column('avg_delta_score', sa.Float(), default=0.0),
        sa.Column('hourly_breakdown', sa.String(), default='[]'),
        sa.Column('category_breakdown', sa.String(), default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_analytics_snapshots_user_id', 'analytics_snapshots', ['user_id'])
    op.create_index('ix_analytics_snapshots_date', 'analytics_snapshots', ['snapshot_date'])
    op.create_index('ix_analytics_snapshots_user_date', 'analytics_snapshots', ['user_id', 'snapshot_date'])


def downgrade() -> None:
    op.drop_table('analytics_snapshots')
