"""
Password reset endpoints.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlmodel import Session, select

from app.api.auth import get_password_hash, verify_password
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_session
from app.models.user import User
from app.services.email_service import email_service

router = APIRouter(prefix="/auth", tags=["auth"])


# In-memory token storage (use Redis in production)
password_reset_tokens: Dict[str, dict] = {}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


def create_password_reset_token(user_id: str) -> str:
    """Create a password reset token valid for 1 hour."""
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=1)
    
    password_reset_tokens[token] = {
        "user_id": user_id,
        "expires": expires
    }
    
    return token


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return user_id if valid."""
    token_data = password_reset_tokens.get(token)
    
    if not token_data:
        return None
    
    if datetime.utcnow() > token_data["expires"]:
        del password_reset_tokens[token]
        return None
    
    return token_data["user_id"]


@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_session)
):
    """Request password reset link."""
    user = db.exec(select(User).where(User.email == request.email)).first()
    
    # Don't reveal if email exists for security
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Create reset token
    token = create_password_reset_token(str(user.id))
    
    # Build reset URL
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    reset_url = f"{frontend_url}/reset-password?token={token}"
    
    # Send email asynchronously
    import asyncio
    asyncio.create_task(
        email_service.send_password_reset(user.email, token, reset_url)
    )
    
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_session)
):
    """Reset password using token."""
    user_id = verify_password_reset_token(request.token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(request.password)
    db.add(user)
    db.commit()
    
    # Invalidate token
    del password_reset_tokens[request.token]
    
    return {"message": "Password reset successfully"}


@router.put("/me/password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Change password for logged-in user."""
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = get_password_hash(request.new_password)
    db.add(current_user)
    db.commit()
    
    return {"message": "Password changed successfully"}
