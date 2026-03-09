"""Add sharing and team collaboration tables.

Revision ID: 018
Revises: 017
Create Date: 2026-02-18 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '018'
down_revision: Union[str, None] = '017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Share links
    op.create_table(
        'share_links',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('owner_id', sa.String(), nullable=False),
        sa.Column('share_type', sa.String(), nullable=False),
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('permission', sa.String(), default='view'),
        sa.Column('password', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('max_views', sa.Integer(), nullable=True),
        sa.Column('view_count', sa.Integer(), default=0),
        sa.Column('allow_comments', sa.Boolean(), default=False),
        sa.Column('allow_download', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    
    op.create_index('ix_share_links_owner', 'share_links', ['owner_id'])
    op.create_index('ix_share_links_token', 'share_links', ['token'])
    
    # Teams
    op.create_table(
        'teams',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('allow_guest_invites', sa.Boolean(), default=True),
        sa.Column('plan', sa.String(), default='free'),
        sa.Column('max_members', sa.Integer(), default=5),
        sa.Column('member_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    
    # Team members
    op.create_table(
        'team_members',
        sa.Column('team_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(), default='member'),
        sa.Column('can_invite', sa.Boolean(), default=False),
        sa.Column('can_manage_content', sa.Boolean(), default=False),
        sa.Column('can_billing', sa.Boolean(), default=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('invited_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('team_id', 'user_id')
    )
    
    # Team invites
    op.create_table(
        'team_invites',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('team_id', sa.String(), nullable=False),
        sa.Column('invited_by', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('role', sa.String(), default='member'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    
    op.create_index('ix_team_invites_team', 'team_invites', ['team_id'])
    op.create_index('ix_team_invites_email', 'team_invites', ['email'])
    
    # Shared collections
    op.create_table(
        'shared_collections',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('team_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('items', sa.String(), default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_shared_collections_team', 'shared_collections', ['team_id'])


def downgrade() -> None:
    op.drop_table('shared_collections')
    op.drop_table('team_invites')
    op.drop_table('team_members')
    op.drop_table('teams')
    op.drop_table('share_links')
