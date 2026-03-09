"""
Stripe billing endpoints for subscriptions.
T057: Stripe integration.
"""
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.auth import get_current_user
from app.core.config import settings
from app.core.database import get_session
from app.models.user import User, UserTier

router = APIRouter(prefix="/billing", tags=["billing"])

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class PlanResponse(BaseModel):
    id: str
    name: str
    description: str
    price_monthly: int  # cents
    price_yearly: int   # cents
    features: list[str]


class CheckoutSessionRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    session_id: str
    url: str


class SubscriptionResponse(BaseModel):
    id: str
    status: str
    current_period_end: int
    cancel_at_period_end: bool
    plan_name: str


class PortalSessionResponse(BaseModel):
    url: str


# Available plans
PLANS = {
    "starter": {
        "id": "starter",
        "name": "Starter",
        "description": "Perfect for individuals getting started",
        "price_monthly": 500,   # $5/month
        "price_yearly": 4800,   # $48/year (20% off)
        "features": [
            "Up to 50 feeds",
            "Daily brief email",
            "$2 AI budget/month",
            "Basic analytics",
        ],
        "stripe_price_id_monthly": "price_starter_monthly",
        "stripe_price_id_yearly": "price_starter_yearly",
    },
    "professional": {
        "id": "professional",
        "name": "Professional",
        "description": "For power users and teams",
        "price_monthly": 1500,  # $15/month
        "price_yearly": 14400,  # $144/year (20% off)
        "features": [
            "Unlimited feeds",
            "Priority AI processing",
            "$10 AI budget/month",
            "Advanced analytics",
            "API access",
        ],
        "stripe_price_id_monthly": "price_pro_monthly",
        "stripe_price_id_yearly": "price_pro_yearly",
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise",
        "description": "Custom solutions for organizations",
        "price_monthly": 5000,  # $50/month
        "price_yearly": 48000,  # $480/year (20% off)
        "features": [
            "Everything in Pro",
            "Custom AI budget",
            "SSO/SAML",
            "Dedicated support",
            "Custom integrations",
        ],
        "stripe_price_id_monthly": "price_enterprise_monthly",
        "stripe_price_id_yearly": "price_enterprise_yearly",
    },
}


@router.get("/plans", response_model=list[PlanResponse])
def list_plans():
    """List available subscription plans."""
    return [
        PlanResponse(
            id=plan["id"],
            name=plan["name"],
            description=plan["description"],
            price_monthly=plan["price_monthly"],
            price_yearly=plan["price_yearly"],
            features=plan["features"],
        )
        for plan in PLANS.values()
    ]


@router.post("/checkout", response_model=CheckoutSessionResponse)
def create_checkout_session(
    req: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
):
    """Create Stripe checkout session for subscription."""
    try:
        # Create or get Stripe customer
        if current_user.stripe_customer_id:
            customer_id = current_user.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": current_user.id},
            )
            customer_id = customer.id
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": req.price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=req.success_url,
            cancel_url=req.cancel_url,
            metadata={"user_id": current_user.id},
        )
        
        return CheckoutSessionResponse(
            session_id=session.id,
            url=session.url,
        )
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/subscription", response_model=Optional[SubscriptionResponse])
def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get current user's subscription."""
    if not current_user.stripe_subscription_id:
        return None
    
    try:
        subscription = stripe.Subscription.retrieve(
            current_user.stripe_subscription_id
        )
        
        # Get plan name from price ID
        plan_name = "Unknown"
        for plan in PLANS.values():
            if subscription["items"]["data"][0]["price"]["id"] in [
                plan["stripe_price_id_monthly"],
                plan["stripe_price_id_yearly"],
            ]:
                plan_name = plan["name"]
                break
        
        return SubscriptionResponse(
            id=subscription.id,
            status=subscription.status,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            plan_name=plan_name,
        )
        
    except stripe.error.StripeError:
        return None


@router.post("/portal", response_model=PortalSessionResponse)
def create_portal_session(
    return_url: str,
    current_user: User = Depends(get_current_user),
):
    """Create Stripe customer portal session."""
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No subscription found",
        )
    
    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=return_url,
        )
        
        return PortalSessionResponse(url=session.url)
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_session)):
    """Handle Stripe webhooks."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle events
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        
        if user_id:
            user = db.exec(select(User).where(User.id == user_id)).first()
            if user:
                user.stripe_customer_id = session.get("customer")
                user.stripe_subscription_id = session.get("subscription")
                
                # Update tier based on plan
                # (would need to lookup price ID to determine tier)
                
                db.add(user)
                db.commit()
    
    elif event["type"] == "invoice.payment_failed":
        subscription = event["data"]["object"]
        # Handle failed payment - notify user
        
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        user_id = subscription.get("metadata", {}).get("user_id")
        
        if user_id:
            user = db.exec(select(User).where(User.id == user_id)).first()
            if user:
                user.tier = UserTier.STARTER
                user.stripe_subscription_id = None
                db.add(user)
                db.commit()
    
    return {"status": "success"}
