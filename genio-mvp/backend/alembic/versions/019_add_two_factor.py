"""Add two-factor authentication and SSO tables.

Revision ID: 019
Revises: 018
Create Date: 2026-02-18 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '019'
down_revision: Union[str, None] = '018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Two-factor auth
    op.create_table(
        'two_factor_auth',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('totp_secret', sa.String(), nullable=True),
        sa.Column('totp_enabled', sa.Boolean(), default=False),
        sa.Column('totp_verified', sa.Boolean(), default=False),
        sa.Column('sms_phone', sa.String(), nullable=True),
        sa.Column('sms_enabled', sa.Boolean(), default=False),
        sa.Column('sms_verified', sa.Boolean(), default=False),
        sa.Column('backup_email', sa.String(), nullable=True),
        sa.Column('email_enabled', sa.Boolean(), default=False),
        sa.Column('webauthn_enabled', sa.Boolean(), default=False),
        sa.Column('backup_codes', sa.String(), default='[]'),
        sa.Column('backup_codes_used', sa.Integer(), default=0),
        sa.Column('preferred_method', sa.String(), default='totp'),
        sa.Column('enabled_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # WebAuthn credentials
    op.create_table(
        'webauthn_credentials',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('credential_id', sa.String(), nullable=False),
        sa.Column('public_key', sa.String(), nullable=False),
        sa.Column('sign_count', sa.Integer(), default=0),
        sa.Column('device_name', sa.String(), nullable=True),
        sa.Column('device_type', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_webauthn_credentials_user', 'webauthn_credentials', ['user_id'])
    op.create_index('ix_webauthn_credentials_credential', 'webauthn_credentials', ['credential_id'])
    
    # Two-factor challenges
    op.create_table(
        'two_factor_challenges',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('challenge_type', sa.String(), nullable=False),
        sa.Column('challenge_token', sa.String(), nullable=False),
        sa.Column('challenge_data', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('code_attempts', sa.Integer(), default=0),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('challenge_token')
    )
    
    op.create_index('ix_2fa_challenges_user', 'two_factor_challenges', ['user_id'])
    op.create_index('ix_2fa_challenges_token', 'two_factor_challenges', ['challenge_token'])
    
    # SSO connections
    op.create_table(
        'sso_connections',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('provider_user_id', sa.String(), nullable=False),
        sa.Column('access_token', sa.String(), nullable=True),
        sa.Column('refresh_token', sa.String(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_sso_connections_user', 'sso_connections', ['user_id'])
    op.create_index('ix_sso_connections_provider', 'sso_connections', ['provider', 'provider_user_id'])
    
    # SSO settings (for teams)
    op.create_table(
        'sso_settings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('team_id', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('client_secret', sa.String(), nullable=False),
        sa.Column('saml_metadata_url', sa.String(), nullable=True),
        sa.Column('saml_certificate', sa.String(), nullable=True),
        sa.Column('enforce_sso', sa.Boolean(), default=False),
        sa.Column('auto_provision', sa.Boolean(), default=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('sso_settings')
    op.drop_table('sso_connections')
    op.drop_table('two_factor_challenges')
    op.drop_table('webauthn_credentials')
    op.drop_table('two_factor_auth')
