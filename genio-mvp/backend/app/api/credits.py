"""
Credit management API endpoints.

This module provides endpoints for:
- Wallet status and balance
- Credit purchases
- Transaction history
- Referral management
- Usage statistics
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.auth import get_current_user
from app.core.config import settings
from app.core.database import get_session
from app.models.credits import (
    CREDIT_COSTS,
    CREDIT_PACKAGES,
    CreditOperationType,
    CreditPackage,
)
from app.models.user import User
from app.services.credit_service import CreditService, get_credit_service

router = APIRouter(prefix="/credits", tags=["credits"])

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# ==================== Request/Response Models ====================

class WalletStatusResponse(BaseModel):
    """Response for wallet status."""
    balance: int
    total_earned: int
    total_spent: int
    monthly_allocation: int
    allocation_resets_at: Optional[datetime]
    current_streak: int
    longest_streak: int
    referral_code: str
    referral_credits_earned: int
    has_low_balance: bool
    is_exhausted: bool


class CreditPackageResponse(BaseModel):
    """Response for credit package info."""
    id: str
    name: str
    credits: int
    bonus_credits: int
    price_cents: int
    price_formatted: str
    features_unlocked: List[str]
    validity_days: int


class PurchaseRequest(BaseModel):
    """Request to purchase credits."""
    package: CreditPackage
    success_url: str
    cancel_url: str


class PurchaseResponse(BaseModel):
    """Response for credit purchase."""
    session_id: str
    url: str
    package: str
    credits: int
    bonus_credits: int


class TransactionResponse(BaseModel):
    """Response for a credit transaction."""
    id: int
    type: str
    operation: Optional[str]
    amount: int
    balance_after: int
    description: Optional[str]
    created_at: datetime


class UsageStatsResponse(BaseModel):
    """Response for usage statistics."""
    period_days: int
    total_spent: int
    total_earned: int
    net_change: int
    by_operation: Dict[str, Dict[str, int]]
    average_daily_spend: float
    projected_monthly_spend: float


class ReferralValidateResponse(BaseModel):
    """Response for referral code validation."""
    valid: bool
    referrer_name: Optional[str] = None
    bonus_credits: int = 50


class OperationCostResponse(BaseModel):
    """Response for operation cost lookup."""
    operation: str
    credits: int
    description: str


# ==================== Endpoints ====================

@router.get("/wallet", response_model=WalletStatusResponse)
def get_wallet_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get current user's credit wallet status."""
    service = get_credit_service(db)
    status = service.get_wallet_status(current_user.id)
    
    return WalletStatusResponse(
        balance=status["balance"],
        total_earned=status["total_earned"],
        total_spent=status["total_spent"],
        monthly_allocation=status["monthly_allocation"],
        allocation_resets_at=status["allocation_resets_at"],
        current_streak=status["current_streak"],
        longest_streak=status["longest_streak"],
        referral_code=status["referral_code"],
        referral_credits_earned=status["referral_credits_earned"],
        has_low_balance=status["has_low_balance"],
        is_exhausted=status["is_exhausted"],
    )


@router.get("/packages", response_model=List[CreditPackageResponse])
def list_credit_packages():
    """List available credit packages for purchase."""
    packages = []
    
    for package_id, info in CREDIT_PACKAGES.items():
        price_dollars = info["price_cents"] / 100
        packages.append(CreditPackageResponse(
            id=package_id.value,
            name=package_id.value.title(),
            credits=info["credits"],
            bonus_credits=info["bonus_credits"],
            price_cents=info["price_cents"],
            price_formatted=f"${price_dollars:.2f}",
            features_unlocked=info["features_unlocked"],
            validity_days=info["validity_days"],
        ))
    
    return packages


@router.post("/purchase", response_model=PurchaseResponse)
def create_purchase(
    request: PurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Create a Stripe checkout session for credit purchase."""
    package_info = CREDIT_PACKAGES.get(request.package)
    
    if not package_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid package: {request.package}",
        )
    
    # Check if user has Stripe customer ID
    if not current_user.stripe_customer_id:
        # Create Stripe customer
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"user_id": current_user.id},
        )
        current_user.stripe_customer_id = customer.id
        db.add(current_user)
        db.commit()
    
    # Create Stripe checkout session
    try:
        session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Genio Credits - {request.package.value.title()}",
                        "description": f"{package_info['credits']:,} credits + {package_info['bonus_credits']:,} bonus",
                    },
                    "unit_amount": package_info["price_cents"],
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "user_id": current_user.id,
                "package": request.package.value,
                "credits": package_info["credits"],
                "bonus_credits": package_info["bonus_credits"],
            },
        )
        
        # Create pending purchase record
        service = get_credit_service(db)
        purchase = service.create_purchase(
            user_id=current_user.id,
            package=request.package,
            stripe_payment_intent_id=session.payment_intent_id or session.id,
        )
        
        return PurchaseResponse(
            session_id=session.id,
            url=session.url,
            package=request.package.value,
            credits=package_info["credits"],
            bonus_credits=package_info["bonus_credits"],
        )
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/purchase/webhook")
async def purchase_webhook(
    request: dict,
    db: Session = Depends(get_session),
):
    """Handle Stripe webhooks for purchase completion."""
    # This would be called by Stripe
    # In production, verify webhook signature
    
    event_type = request.get("type")
    
    if event_type == "checkout.session.completed":
        session = request.get("data", {}).get("object", {})
        metadata = session.get("metadata", {})
        
        user_id = metadata.get("user_id")
        package_str = metadata.get("package")
        
        if user_id and package_str:
            service = get_credit_service(db)
            
            # Find pending purchase
            from app.models.credits import CreditPurchase
            from sqlmodel import select
            
            purchase = db.exec(
                select(CreditPurchase)
                .where(CreditPurchase.user_id == user_id)
                .where(CreditPurchase.payment_status == "pending")
                .where(CreditPurchase.package == CreditPackage(package_str))
                .order_by(CreditPurchase.created_at.desc())
            ).first()
            
            if purchase:
                charge_id = session.get("payment_intent") or session.get("id")
                service.complete_purchase(purchase.id, charge_id)
    
    return {"status": "success"}


@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get user's credit transaction history."""
    from sqlmodel import select
    from app.models.credits import CreditWallet, CreditTransaction
    
    wallet = db.exec(
        select(CreditWallet).where(CreditWallet.user_id == current_user.id)
    ).first()
    
    if not wallet:
        return []
    
    transactions = db.exec(
        select(CreditTransaction)
        .where(CreditTransaction.wallet_id == wallet.id)
        .order_by(CreditTransaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    
    return [
        TransactionResponse(
            id=t.id,
            type=t.type.value,
            operation=t.operation.value if t.operation else None,
            amount=t.amount,
            balance_after=t.balance_after,
            description=t.description,
            created_at=t.created_at,
        )
        for t in transactions
    ]


@router.get("/usage", response_model=UsageStatsResponse)
def get_usage_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get user's credit usage statistics."""
    service = get_credit_service(db)
    stats = service.get_credit_usage_stats(current_user.id, days)
    
    return UsageStatsResponse(
        period_days=stats["period_days"],
        total_spent=stats["total_spent"],
        total_earned=stats["total_earned"],
        net_change=stats["net_change"],
        by_operation=stats["by_operation"],
        average_daily_spend=stats["average_daily_spend"],
        projected_monthly_spend=stats["projected_monthly_spend"],
    )


@router.get("/referral/validate/{code}", response_model=ReferralValidateResponse)
def validate_referral_code(
    code: str,
    db: Session = Depends(get_session),
):
    """Validate a referral code."""
    from sqlmodel import select
    from app.models.credits import CreditWallet
    
    wallet = db.exec(
        select(CreditWallet).where(CreditWallet.referral_code == code)
    ).first()
    
    if not wallet:
        return ReferralValidateResponse(valid=False)
    
    # Get referrer name (optional, for display)
    from app.models.user import User
    referrer = db.get(User, wallet.user_id)
    referrer_name = referrer.first_name if referrer else None
    
    return ReferralValidateResponse(
        valid=True,
        referrer_name=referrer_name,
        bonus_credits=50,  # Standard new user bonus
    )


@router.post("/streak/record")
def record_daily_streak(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Record daily activity for streak tracking."""
    service = get_credit_service(db)
    streak, bonus = service.record_daily_activity(current_user.id)
    
    return {
        "current_streak": streak,
        "bonus_credits_awarded": bonus,
    }


@router.get("/costs", response_model=List[OperationCostResponse])
def list_operation_costs():
    """List credit costs for all operations."""
    descriptions = {
        CreditOperationType.BRIEF_SIMPLE: "Basic daily brief with Llama 3.1",
        CreditOperationType.BRIEF_ADVANCED: "Advanced brief with DeepSeek",
        CreditOperationType.BRIEF_PREMIUM: "Premium brief with GPT-4o",
        CreditOperationType.SEARCH_SEMANTIC: "Semantic search query",
        CreditOperationType.SUMMARIZE: "Article summarization",
        CreditOperationType.EXPLAIN_CONCEPT: "Concept explanation",
        CreditOperationType.FLASHCARD_GENERATE: "Flashcard generation",
        CreditOperationType.EMBEDDING_GENERATE: "Vector embedding generation",
        CreditOperationType.TTS_PIPER: "TTS per 1000 chars (Piper)",
        CreditOperationType.TTS_PLAYHT: "TTS per 1000 chars (PlayHT)",
        CreditOperationType.TTS_ELEVENLABS: "TTS per 1000 chars (ElevenLabs)",
        CreditOperationType.STORAGE_MB: "Storage per MB per month",
        CreditOperationType.EXPORT_PDF: "PDF export with AI",
        CreditOperationType.TEAM_SHARE: "Team sharing operation",
        CreditOperationType.API_CALL: "API call",
        CreditOperationType.DOCUMENT_UPLOAD: "Document upload",
        CreditOperationType.DOCUMENT_OCR: "OCR processing",
        CreditOperationType.DOCUMENT_ANALYZE: "AI document analysis",
        CreditOperationType.KNOWLEDGE_GRAPH: "Knowledge graph query",
    }
    
    return [
        OperationCostResponse(
            operation=op.value,
            credits=credits,
            description=descriptions.get(op, ""),
        )
        for op, credits in CREDIT_COSTS.items()
    ]


@router.get("/check/{operation}")
def check_can_afford(
    operation: str,
    quantity: int = Query(1, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Check if user can afford an operation."""
    service = get_credit_service(db)
    
    try:
        op_type = CreditOperationType(operation)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation: {operation}",
        )
    
    can_afford, credits_needed = service.can_afford(
        user_id=current_user.id,
        operation=op_type,
        quantity=quantity,
    )
    
    return {
        "can_afford": can_afford,
        "credits_needed": credits_needed,
        "current_balance": service.get_or_create_wallet(current_user.id).balance,
    }
