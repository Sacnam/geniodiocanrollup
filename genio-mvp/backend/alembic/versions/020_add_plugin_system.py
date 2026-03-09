"""Add plugin system tables.

Revision ID: 020
Revises: 019
Create Date: 2026-02-18 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '020'
down_revision: Union[str, None] = '019'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Plugins
    op.create_table(
        'plugins',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('manifest_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('author', sa.String(), nullable=False),
        sa.Column('plugin_type', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('status', sa.String(), default='inactive'),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('settings', sa.String(), default='{}'),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('is_enabled', sa.Boolean(), default=False),
        sa.Column('last_executed_at', sa.DateTime(), nullable=True),
        sa.Column('execution_count', sa.Integer(), default=0),
        sa.Column('error_count', sa.Integer(), default=0),
        sa.Column('installed_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_plugins_manifest', 'plugins', ['manifest_id'])
    op.create_index('ix_plugins_type', 'plugins', ['plugin_type'])
    
    # User plugins
    op.create_table(
        'user_plugins',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('plugin_id', sa.String(), nullable=False),
        sa.Column('settings', sa.String(), default='{}'),
        sa.Column('is_enabled', sa.Boolean(), default=True),
        sa.Column('sidebar_position', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'plugin_id')
    )
    
    # Plugin execution logs
    op.create_table(
        'plugin_execution_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('plugin_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('trigger', sa.String(), nullable=False),
        sa.Column('hook_name', sa.String(), nullable=True),
        sa.Column('input_data', sa.String(), default='{}'),
        sa.Column('output_data', sa.String(), default='{}'),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_plugin_logs_plugin', 'plugin_execution_logs', ['plugin_id'])
    op.create_index('ix_plugin_logs_user', 'plugin_execution_logs', ['user_id'])
    
    # Plugin webhooks
    op.create_table(
        'plugin_webhooks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('plugin_id', sa.String(), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('secret', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_called_at', sa.DateTime(), nullable=True),
        sa.Column('call_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_plugin_webhooks_plugin', 'plugin_webhooks', ['plugin_id'])


def downgrade() -> None:
    op.drop_table('plugin_webhooks')
    op.drop_table('plugin_execution_logs')
    op.drop_table('user_plugins')
    op.drop_table('plugins')
