from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.core.auth import get_current_user, get_current_user_id
from app.core.database import get_db
from app.models.user import User

router = APIRouter()


class UserSettings(BaseModel):
    timezone: Optional[str] = None
    brief_delivery_time: Optional[str] = None  # HH:MM
    brief_email_enabled: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserSettingsResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    timezone: str
    brief_delivery_time: str
    brief_email_enabled: bool
    tier: str
    budget_remaining: float
    budget_percentage: float


class BudgetStatus(BaseModel):
    total: float
    used: float
    remaining: float
    percentage_remaining: float
    level: str  # L1, L2, L3


@router.get("/settings", response_model=UserSettingsResponse)
async def get_settings(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user settings."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserSettingsResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        timezone=user.timezone,
        brief_delivery_time=user.brief_delivery_time,
        brief_email_enabled=user.brief_email_enabled,
        tier=user.tier.value,
        budget_remaining=user.budget_remaining,
        budget_percentage=user.budget_percentage_remaining,
    )


@router.put("/settings")
async def update_settings(
    data: UserSettings,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update user settings."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if data.timezone is not None:
        user.timezone = data.timezone
    if data.brief_delivery_time is not None:
        user.brief_delivery_time = data.brief_delivery_time
    if data.brief_email_enabled is not None:
        user.brief_email_enabled = data.brief_email_enabled
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"status": "updated"}


@router.get("/budget", response_model=BudgetStatus)
async def get_budget(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get AI budget status."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    percentage = user.budget_percentage_remaining
    
    # Determine level (B12)
    if percentage > 50:
        level = "L1"  # Full AI
    elif percentage > 20:
        level = "L2"  # Reduced AI
    else:
        level = "L3"  # No AI
    
    return BudgetStatus(
        total=user.monthly_ai_budget,
        used=user.ai_budget_used_this_month,
        remaining=user.budget_remaining,
        percentage_remaining=percentage,
        level=level,
    )


@router.get("/profile")
async def get_profile(
    user: User = Depends(get_current_user),
):
    """Get user profile."""
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "tier": user.tier.value,
        "created_at": user.created_at,
    }
