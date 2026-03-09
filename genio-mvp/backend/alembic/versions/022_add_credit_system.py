"""Add credit-based sustainability system.

Revision ID: 022
Revises: 021
Create Date: 2024-02-18 00:00:00.000000

This migration adds:
- Credit wallets for tracking user balances
- Credit transactions for audit trail
- Credit purchases for payment tracking
- User streaks for gamification
- Referrals for growth

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade():
    # Credit wallets table
    op.create_table('credit_wallets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('balance', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_spent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_allocation', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('allocation_resets_at', sa.DateTime(), nullable=True),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_activity_date', sa.DateTime(), nullable=True),
        sa.Column('referral_code', sa.String(), nullable=False),
        sa.Column('referral_credits_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('referral_code')
    )
    
    op.create_index('ix_credit_wallets_user_id', 'credit_wallets', ['user_id'], unique=True)
    op.create_index('ix_credit_wallets_referral_code', 'credit_wallets', ['referral_code'], unique=True)
    
    # Credit transactions table
    op.create_table('credit_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wallet_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('operation', sa.String(), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('reference_id', sa.String(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('stripe_payment_id', sa.String(), nullable=True),
        sa.Column('package', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['wallet_id'], ['credit_wallets.id'], ondelete='CASCADE')
    )
    
    op.create_index('ix_credit_transactions_wallet_id', 'credit_transactions', ['wallet_id'])
    op.create_index('ix_credit_transactions_type', 'credit_transactions', ['type'])
    op.create_index('ix_credit_transactions_created_at', 'credit_transactions', ['created_at'])
    
    # Credit purchases table
    op.create_table('credit_purchases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('package', sa.String(), nullable=False),
        sa.Column('credits_purchased', sa.Integer(), nullable=False),
        sa.Column('bonus_credits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('price_cents', sa.Integer(), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(), nullable=True),
        sa.Column('stripe_charge_id', sa.String(), nullable=True),
        sa.Column('payment_status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('credits_expire_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    op.create_index('ix_credit_purchases_user_id', 'credit_purchases', ['user_id'])
    
    # User streaks table
    op.create_table('user_streaks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_activity_date', sa.DateTime(), nullable=True),
        sa.Column('streak_7_rewarded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('streak_30_rewarded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('streak_90_rewarded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id')
    )
    
    op.create_index('ix_user_streaks_user_id', 'user_streaks', ['user_id'], unique=True)
    
    # Referrals table
    op.create_table('referrals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('referrer_id', sa.String(), nullable=False),
        sa.Column('referred_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('qualified_at', sa.DateTime(), nullable=True),
        sa.Column('referrer_credits', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('referred_credits', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('rewarded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['referrer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['referred_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('referred_id')
    )
    
    op.create_index('ix_referrals_referrer_id', 'referrals', ['referrer_id'])
    op.create_index('ix_referrals_referred_id', 'referrals', ['referred_id'], unique=True)
    
    # Add credit-related fields to users table
    op.add_column('users', sa.Column('credit_tier', sa.String(), nullable=True, server_default='free'))
    op.add_column('users', sa.Column('features_unlocked', postgresql.JSONB(), nullable=True, server_default='[]'))


def downgrade():
    # Remove user columns
    op.drop_column('users', 'features_unlocked')
    op.drop_column('users', 'credit_tier')
    
    # Drop tables in reverse order
    op.drop_table('referrals')
    op.drop_table('user_streaks')
    op.drop_table('credit_purchases')
    op.drop_table('credit_transactions')
    op.drop_table('credit_wallets')
