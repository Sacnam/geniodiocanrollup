"""Add brief templates table.

Revision ID: 017
Revises: 016
Create Date: 2026-02-18 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '017'
down_revision: Union[str, None] = '016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'brief_templates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('layout', sa.String(), default='standard'),
        sa.Column('accent_color', sa.String(), nullable=True),
        sa.Column('max_articles', sa.Integer(), default=10),
        sa.Column('min_delta_score', sa.Float(), default=0.0),
        sa.Column('include_read', sa.Boolean(), default=False),
        sa.Column('delivery_time', sa.String(), default='08:00'),
        sa.Column('delivery_days', sa.String(), default='[1,2,3,4,5]'),
        sa.Column('timezone', sa.String(), default='UTC'),
        sa.Column('sections', sa.String(), default='[]'),
        sa.Column('preferred_categories', sa.String(), default='[]'),
        sa.Column('excluded_categories', sa.String(), default='[]'),
        sa.Column('preferred_feeds', sa.String(), default='[]'),
        sa.Column('excluded_feeds', sa.String(), default='[]'),
        sa.Column('ai_summary_length', sa.String(), default='medium'),
        sa.Column('ai_persona', sa.String(), nullable=True),
        sa.Column('ai_focus_areas', sa.String(), default='[]'),
        sa.Column('generated_count', sa.Integer(), default=0),
        sa.Column('last_generated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_brief_templates_user_id', 'brief_templates', ['user_id'])
    op.create_index('ix_brief_templates_default', 'brief_templates', ['user_id', 'is_default'])


def downgrade() -> None:
    op.drop_table('brief_templates')
