"""
Credit management service for Genio Knowledge OS.

This module handles:
- Credit wallet management
- Credit transactions (earning and spending)
- Monthly allocations
- Streak bonuses
- Referral rewards
- Credit purchases
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlmodel import Session, select

from app.models.credits import (
    CREDIT_COSTS,
    CREDIT_PACKAGES,
    MONTHLY_CREDIT_ALLOCATION,
    CreditOperationType,
    CreditPackage,
    CreditTransaction,
    CreditTransactionType,
    CreditWallet,
    CreditPurchase,
    Referral,
    UserStreak,
)

logger = structlog.get_logger()


class CreditService:
    """
    Service for managing user credits.
    
    Key responsibilities:
    1. Wallet initialization and management
    2. Credit consumption tracking
    3. Monthly allocation resets
    4. Streak and referral bonuses
    5. Purchase processing
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== Wallet Management ====================
    
    def get_or_create_wallet(self, user_id: str, tier: str = "free") -> CreditWallet:
        """Get or create a credit wallet for a user."""
        wallet = self.db.exec(
            select(CreditWallet).where(CreditWallet.user_id == user_id)
        ).first()
        
        if not wallet:
            wallet = self._create_wallet(user_id, tier)
        
        return wallet
    
    def _create_wallet(self, user_id: str, tier: str) -> CreditWallet:
        """Create a new credit wallet."""
        monthly_allocation = MONTHLY_CREDIT_ALLOCATION.get(tier, 50)
        
        wallet = CreditWallet(
            user_id=user_id,
            balance=monthly_allocation,  # Start with monthly allocation
            total_earned=monthly_allocation,
            monthly_allocation=monthly_allocation,
            allocation_resets_at=self._next_month_reset(),
            referral_code=self._generate_referral_code(user_id),
        )
        
        self.db.add(wallet)
        
        # Record initial allocation
        self._record_transaction(
            wallet=wallet,
            type=CreditTransactionType.MONTHLY_ALLOCATION,
            amount=monthly_allocation,
            description=f"Initial monthly allocation ({tier} tier)",
        )
        
        self.db.commit()
        self.db.refresh(wallet)
        
        logger.info(
            "wallet_created",
            user_id=user_id,
            tier=tier,
            initial_balance=monthly_allocation,
        )
        
        return wallet
    
    def _generate_referral_code(self, user_id: str) -> str:
        """Generate a unique referral code for a user."""
        # Use user_id + random for uniqueness
        base = f"{user_id}:{secrets.token_hex(4)}"
        code_hash = hashlib.sha256(base.encode()).hexdigest()[:8].upper()
        return f"GENIO-{code_hash}"
    
    def _next_month_reset(self) -> datetime:
        """Calculate next monthly reset date."""
        now = datetime.utcnow()
        # First day of next month
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
        return next_month
    
    # ==================== Credit Consumption ====================
    
    def can_afford(
        self,
        user_id: str,
        operation: CreditOperationType,
        quantity: int = 1,
    ) -> Tuple[bool, int]:
        """
        Check if user can afford an operation.
        
        Args:
            user_id: User ID
            operation: Operation type
            quantity: Number of units (e.g., characters for TTS)
            
        Returns:
            Tuple of (can_afford, credits_needed)
        """
        wallet = self.get_or_create_wallet(user_id)
        
        # Get base cost
        base_cost = CREDIT_COSTS.get(operation, 5)
        
        # Calculate total cost
        if operation in [CreditOperationType.TTS_PIPER, CreditOperationType.TTS_PLAYHT, CreditOperationType.TTS_ELEVENLABS]:
            # TTS costs are per 1000 characters
            credits_needed = max(1, (quantity // 1000) * base_cost)
        elif operation == CreditOperationType.STORAGE_MB:
            # Storage is per MB
            credits_needed = quantity * base_cost
        else:
            credits_needed = base_cost
        
        return wallet.balance >= credits_needed, credits_needed
    
    def consume_credits(
        self,
        user_id: str,
        operation: CreditOperationType,
        estimated_credits: int,
        actual_credits: Optional[int] = None,
        reference_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> CreditTransaction:
        """
        Consume credits for an operation.
        
        Args:
            user_id: User ID
            operation: Operation type
            estimated_credits: Pre-estimated credits
            actual_credits: Actual credits (if different from estimate)
            reference_id: Related entity ID
            metadata: Additional metadata
            
        Returns:
            CreditTransaction record
        """
        wallet = self.get_or_create_wallet(user_id)
        
        # Use actual credits if provided, otherwise estimate
        credits_to_deduct = actual_credits if actual_credits is not None else estimated_credits
        
        if wallet.balance < credits_to_deduct:
            raise InsufficientCreditsError(
                f"Insufficient credits: need {credits_to_deduct}, have {wallet.balance}"
            )
        
        # Deduct from wallet
        wallet.balance -= credits_to_deduct
        wallet.total_spent += credits_to_deduct
        
        # Record transaction
        transaction = self._record_transaction(
            wallet=wallet,
            type=CreditTransactionType.OPERATION,
            amount=-credits_to_deduct,
            operation=operation,
            reference_id=reference_id,
            metadata=metadata,
        )
        
        self.db.add(wallet)
        self.db.commit()
        
        logger.info(
            "credits_consumed",
            user_id=user_id,
            operation=operation.value,
            credits=credits_to_deduct,
            remaining_balance=wallet.balance,
        )
        
        return transaction
    
    def refund_credits(
        self,
        user_id: str,
        credits: int,
        reason: str,
        reference_id: Optional[str] = None,
    ) -> CreditTransaction:
        """Refund credits to a user's wallet."""
        wallet = self.get_or_create_wallet(user_id)
        
        wallet.balance += credits
        wallet.total_earned += credits
        
        transaction = self._record_transaction(
            wallet=wallet,
            type=CreditTransactionType.REFUND,
            amount=credits,
            description=reason,
            reference_id=reference_id,
        )
        
        self.db.add(wallet)
        self.db.commit()
        
        return transaction
    
    # ==================== Monthly Allocations ====================
    
    def check_and_reset_monthly(self, user_id: str) -> bool:
        """
        Check if monthly allocation needs reset and do it.
        
        Returns:
            True if reset was performed
        """
        wallet = self.get_or_create_wallet(user_id)
        
        if not wallet.allocation_resets_at:
            wallet.allocation_resets_at = self._next_month_reset()
            self.db.add(wallet)
            self.db.commit()
            return False
        
        if datetime.utcnow() < wallet.allocation_resets_at:
            return False
        
        # Time to reset
        old_reset = wallet.allocation_resets_at
        wallet.allocation_resets_at = self._next_month_reset()
        
        # Add monthly allocation
        wallet.balance += wallet.monthly_allocation
        wallet.total_earned += wallet.monthly_allocation
        
        self._record_transaction(
            wallet=wallet,
            type=CreditTransactionType.MONTHLY_ALLOCATION,
            amount=wallet.monthly_allocation,
            description=f"Monthly allocation reset",
        )
        
        self.db.add(wallet)
        self.db.commit()
        
        logger.info(
            "monthly_allocation_reset",
            user_id=user_id,
            credits_added=wallet.monthly_allocation,
            new_balance=wallet.balance,
        )
        
        return True
    
    def update_tier(self, user_id: str, new_tier: str) -> None:
        """Update user's tier and monthly allocation."""
        wallet = self.get_or_create_wallet(user_id)
        
        new_allocation = MONTHLY_CREDIT_ALLOCATION.get(new_tier, 50)
        old_allocation = wallet.monthly_allocation
        
        wallet.monthly_allocation = new_allocation
        
        # If upgrading, add the difference immediately
        if new_allocation > old_allocation:
            difference = new_allocation - old_allocation
            wallet.balance += difference
            wallet.total_earned += difference
            
            self._record_transaction(
                wallet=wallet,
                type=CreditTransactionType.ADMIN_GRANT,
                amount=difference,
                description=f"Tier upgrade bonus ({new_tier})",
            )
        
        self.db.add(wallet)
        self.db.commit()
    
    # ==================== Streak System ====================
    
    def record_daily_activity(self, user_id: str) -> Tuple[int, int]:
        """
        Record daily activity for streak tracking.
        
        Returns:
            Tuple of (current_streak, bonus_credits_awarded)
        """
        wallet = self.get_or_create_wallet(user_id)
        
        # Get or create streak record
        streak = self.db.exec(
            select(UserStreak).where(UserStreak.user_id == user_id)
        ).first()
        
        if not streak:
            streak = UserStreak(user_id=user_id)
            self.db.add(streak)
        
        today = datetime.utcnow().date()
        last_activity = streak.last_activity_date.date() if streak.last_activity_date else None
        
        bonus_credits = 0
        
        if last_activity == today:
            # Already recorded today
            return streak.current_streak, 0
        
        if last_activity == today - timedelta(days=1):
            # Consecutive day
            streak.current_streak += 1
        else:
            # Streak broken
            streak.current_streak = 1
        
        streak.last_activity_date = datetime.utcnow()
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        
        # Check for milestone rewards
        if streak.current_streak >= 7 and not streak.streak_7_rewarded:
            bonus_credits += 10
            streak.streak_7_rewarded = True
        
        if streak.current_streak >= 30 and not streak.streak_30_rewarded:
            bonus_credits += 50
            streak.streak_30_rewarded = True
        
        if streak.current_streak >= 90 and not streak.streak_90_rewarded:
            bonus_credits += 200
            streak.streak_90_rewarded = True
        
        # Award bonus credits
        if bonus_credits > 0:
            wallet.balance += bonus_credits
            wallet.total_earned += bonus_credits
            
            self._record_transaction(
                wallet=wallet,
                type=CreditTransactionType.STREAK_BONUS,
                amount=bonus_credits,
                description=f"Streak bonus ({streak.current_streak} days)",
            )
            
            logger.info(
                "streak_bonus_awarded",
                user_id=user_id,
                streak=streak.current_streak,
                bonus=bonus_credits,
            )
        
        # Update wallet streak tracking
        wallet.current_streak = streak.current_streak
        wallet.longest_streak = streak.longest_streak
        wallet.last_activity_date = datetime.utcnow()
        
        self.db.add(streak)
        self.db.add(wallet)
        self.db.commit()
        
        return streak.current_streak, bonus_credits
    
    # ==================== Referral System ====================
    
    def process_referral(
        self,
        referrer_code: str,
        referred_user_id: str,
    ) -> Tuple[bool, int]:
        """
        Process a referral when a new user signs up.
        
        Args:
            referrer_code: Referrer's referral code
            referred_user_id: New user's ID
            
        Returns:
            Tuple of (success, credits_for_new_user)
        """
        # Find referrer
        referrer_wallet = self.db.exec(
            select(CreditWallet).where(CreditWallet.referral_code == referrer_code)
        ).first()
        
        if not referrer_wallet:
            return False, 0
        
        # Check if already referred
        existing = self.db.exec(
            select(Referral).where(Referral.referred_id == referred_user_id)
        ).first()
        
        if existing:
            return False, 0
        
        # Create referral record
        referral = Referral(
            referrer_id=referrer_wallet.user_id,
            referred_id=referred_user_id,
            status="pending",
        )
        self.db.add(referral)
        
        # Give new user their bonus immediately
        new_user_wallet = self.get_or_create_wallet(referred_user_id)
        new_user_bonus = referral.referred_credits  # 50 GC
        
        new_user_wallet.balance += new_user_bonus
        new_user_wallet.total_earned += new_user_bonus
        
        self._record_transaction(
            wallet=new_user_wallet,
            type=CreditTransactionType.REFERRAL_BONUS,
            amount=new_user_bonus,
            description="Welcome bonus from referral",
            reference_id=str(referral.id) if referral.id else None,
        )
        
        self.db.add(new_user_wallet)
        self.db.commit()
        
        logger.info(
            "referral_created",
            referrer_id=referrer_wallet.user_id,
            referred_id=referred_user_id,
            new_user_bonus=new_user_bonus,
        )
        
        return True, new_user_bonus
    
    def qualify_referral(self, referred_user_id: str) -> bool:
        """
        Qualify a referral when the referred user makes their first purchase.
        
        Args:
            referred_user_id: The referred user's ID
            
        Returns:
            True if referral was qualified and rewarded
        """
        referral = self.db.exec(
            select(Referral).where(Referral.referred_id == referred_user_id)
        ).first()
        
        if not referral or referral.status != "pending":
            return False
        
        # Update referral status
        referral.status = "qualified"
        referral.qualified_at = datetime.utcnow()
        
        # Reward the referrer
        referrer_wallet = self.get_or_create_wallet(referral.referrer_id)
        referrer_bonus = referral.referrer_credits  # 100 GC
        
        referrer_wallet.balance += referrer_bonus
        referrer_wallet.total_earned += referrer_bonus
        referrer_wallet.referral_credits_earned += referrer_bonus
        
        self._record_transaction(
            wallet=referrer_wallet,
            type=CreditTransactionType.REFERRAL_BONUS,
            amount=referrer_bonus,
            description="Referral bonus - friend made purchase",
            reference_id=str(referral.id) if referral.id else None,
        )
        
        referral.status = "rewarded"
        referral.rewarded_at = datetime.utcnow()
        
        self.db.add(referral)
        self.db.add(referrer_wallet)
        self.db.commit()
        
        logger.info(
            "referral_qualified",
            referrer_id=referral.referrer_id,
            referred_id=referred_user_id,
            referrer_bonus=referrer_bonus,
        )
        
        return True
    
    # ==================== Purchase System ====================
    
    def create_purchase(
        self,
        user_id: str,
        package: CreditPackage,
        stripe_payment_intent_id: str,
    ) -> CreditPurchase:
        """Create a pending credit purchase."""
        package_info = CREDIT_PACKAGES[package]
        
        purchase = CreditPurchase(
            user_id=user_id,
            package=package,
            credits_purchased=package_info["credits"],
            bonus_credits=package_info["bonus_credits"],
            price_cents=package_info["price_cents"],
            stripe_payment_intent_id=stripe_payment_intent_id,
            credits_expire_at=datetime.utcnow() + timedelta(days=package_info["validity_days"]),
        )
        
        self.db.add(purchase)
        self.db.commit()
        self.db.refresh(purchase)
        
        return purchase
    
    def complete_purchase(
        self,
        purchase_id: int,
        stripe_charge_id: str,
    ) -> Tuple[CreditWallet, int]:
        """
        Complete a credit purchase after payment confirmation.
        
        Returns:
            Tuple of (wallet, total_credits_added)
        """
        purchase = self.db.get(CreditPurchase, purchase_id)
        
        if not purchase or purchase.payment_status != "pending":
            raise ValueError("Invalid purchase or already completed")
        
        # Update purchase status
        purchase.payment_status = "completed"
        purchase.stripe_charge_id = stripe_charge_id
        purchase.completed_at = datetime.utcnow()
        
        # Add credits to wallet
        wallet = self.get_or_create_wallet(purchase.user_id)
        total_credits = purchase.credits_purchased + purchase.bonus_credits
        
        wallet.balance += total_credits
        wallet.total_earned += total_credits
        
        # Record transaction
        self._record_transaction(
            wallet=wallet,
            type=CreditTransactionType.PURCHASE,
            amount=total_credits,
            description=f"Purchased {purchase.package.value} package",
            stripe_payment_id=stripe_charge_id,
            package=purchase.package,
            expires_at=purchase.credits_expire_at,
        )
        
        self.db.add(purchase)
        self.db.add(wallet)
        self.db.commit()
        
        # Check if this qualifies any pending referrals
        self.qualify_referral(purchase.user_id)
        
        logger.info(
            "purchase_completed",
            user_id=purchase.user_id,
            package=purchase.package.value,
            credits_added=total_credits,
        )
        
        return wallet, total_credits
    
    # ==================== Utility Methods ====================
    
    def _record_transaction(
        self,
        wallet: CreditWallet,
        type: CreditTransactionType,
        amount: int,
        operation: Optional[CreditOperationType] = None,
        description: Optional[str] = None,
        reference_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        stripe_payment_id: Optional[str] = None,
        package: Optional[CreditPackage] = None,
        expires_at: Optional[datetime] = None,
    ) -> CreditTransaction:
        """Record a credit transaction."""
        import json
        
        transaction = CreditTransaction(
            wallet_id=wallet.id,
            type=type,
            operation=operation,
            amount=amount,
            balance_after=wallet.balance + amount,  # New balance after this transaction
            description=description,
            reference_id=reference_id,
            metadata_json=json.dumps(metadata) if metadata else None,
            stripe_payment_id=stripe_payment_id,
            package=package,
            expires_at=expires_at,
        )
        
        self.db.add(transaction)
        return transaction
    
    def get_wallet_status(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive wallet status for a user."""
        wallet = self.get_or_create_wallet(user_id)
        
        # Check for monthly reset
        self.check_and_reset_monthly(user_id)
        
        # Get recent transactions
        recent_transactions = self.db.exec(
            select(CreditTransaction)
            .where(CreditTransaction.wallet_id == wallet.id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(10)
        ).all()
        
        return {
            "balance": wallet.balance,
            "total_earned": wallet.total_earned,
            "total_spent": wallet.total_spent,
            "monthly_allocation": wallet.monthly_allocation,
            "allocation_resets_at": wallet.allocation_resets_at,
            "current_streak": wallet.current_streak,
            "longest_streak": wallet.longest_streak,
            "referral_code": wallet.referral_code,
            "referral_credits_earned": wallet.referral_credits_earned,
            "has_low_balance": wallet.has_low_balance,
            "is_exhausted": wallet.is_exhausted,
            "recent_transactions": [
                {
                    "type": t.type.value,
                    "operation": t.operation.value if t.operation else None,
                    "amount": t.amount,
                    "balance_after": t.balance_after,
                    "description": t.description,
                    "created_at": t.created_at.isoformat(),
                }
                for t in recent_transactions
            ],
        }
    
    def get_credit_usage_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get credit usage statistics for a user."""
        wallet = self.get_or_create_wallet(user_id)
        
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get transactions in period
        transactions = self.db.exec(
            select(CreditTransaction)
            .where(CreditTransaction.wallet_id == wallet.id)
            .where(CreditTransaction.created_at >= since)
        ).all()
        
        # Calculate stats
        total_spent = sum(t.amount for t in transactions if t.amount < 0)
        total_earned = sum(t.amount for t in transactions if t.amount > 0)
        
        # Group by operation
        by_operation = {}
        for t in transactions:
            if t.operation:
                op = t.operation.value
                if op not in by_operation:
                    by_operation[op] = {"count": 0, "credits": 0}
                by_operation[op]["count"] += 1
                by_operation[op]["credits"] += abs(t.amount)
        
        return {
            "period_days": days,
            "total_spent": abs(total_spent),
            "total_earned": total_earned,
            "net_change": total_earned + total_spent,  # spent is negative
            "by_operation": by_operation,
            "average_daily_spend": abs(total_spent) / days if days > 0 else 0,
            "projected_monthly_spend": (abs(total_spent) / days) * 30 if days > 0 else 0,
        }


class InsufficientCreditsError(Exception):
    """Raised when user doesn't have enough credits."""
    pass


# Factory function for dependency injection
def get_credit_service(db: Session) -> CreditService:
    """Get a CreditService instance."""
    return CreditService(db)