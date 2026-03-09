"""Add keyboard shortcuts configuration.

Revision ID: 015
Revises: 014
Create Date: 2026-02-18 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '015'
down_revision: Union[str, None] = '014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'keyboard_shortcuts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('config', sa.String(), default='{}'),
        sa.Column('version', sa.String(), default='1.0'),
        sa.Column('vim_mode_enabled', sa.Boolean(), default=True),
        sa.Column('custom_bindings', sa.String(), default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    op.create_index('ix_keyboard_shortcuts_user_id', 'keyboard_shortcuts', ['user_id'])


def downgrade() -> None:
    op.drop_table('keyboard_shortcuts')
