"""Add tagging system.

Revision ID: 011
Revises: 010
Create Date: 2026-02-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('parent_id', sa.String(), nullable=True),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_tags_user_id', 'tags', ['user_id'])
    op.create_index('ix_tags_slug', 'tags', ['slug'])
    op.create_index('ix_tags_name', 'tags', ['name'])
    
    # Create article_tags table
    op.create_table(
        'article_tags',
        sa.Column('article_id', sa.String(), nullable=False),
        sa.Column('tag_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('article_id', 'tag_id')
    )
    
    # Create indexes
    op.create_index('ix_article_tags_user_id', 'article_tags', ['user_id'])
    op.create_index('ix_article_tags_tag_id', 'article_tags', ['tag_id'])
    
    # Create document_tags table
    op.create_table(
        'document_tags',
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('tag_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('document_id', 'tag_id')
    )
    
    op.create_index('ix_document_tags_user_id', 'document_tags', ['user_id'])
    op.create_index('ix_document_tags_tag_id', 'document_tags', ['tag_id'])
    
    # Create reading_list_tags table
    op.create_table(
        'reading_list_tags',
        sa.Column('reading_list_id', sa.String(), nullable=False),
        sa.Column('tag_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('reading_list_id', 'tag_id')
    )
    
    op.create_index('ix_reading_list_tags_user_id', 'reading_list_tags', ['user_id'])
    op.create_index('ix_reading_list_tags_tag_id', 'reading_list_tags', ['tag_id'])


def downgrade() -> None:
    op.drop_table('reading_list_tags')
    op.drop_table('document_tags')
    op.drop_table('article_tags')
    op.drop_table('tags')
