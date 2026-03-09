"""
API Dependencies - Common dependencies for API endpoints.
"""
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.auth import verify_token
from app.models.user import User


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from token.
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    
    return user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User object or None
    """
    if not token:
        return None
    
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        return db.get(User, user_id)
    except:
        return None


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require admin privileges.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object
        
    Raises:
        HTTPException: If user is not admin
    """
    # Check if user is admin
    # For now, simple check - can be expanded
    if not getattr(current_user, 'is_admin', False):
        # Also check email domain or list
        admin_emails = getattr(settings, 'ADMIN_EMAILS', '').split(',')
        if current_user.email not in admin_emails:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required",
            )
    
    return current_user


def get_pagination_params(
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """
    Get pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        per_page: Items per page
        
    Returns:
        Pagination params dict
    """
    return {
        "page": max(1, page),
        "per_page": min(max(1, per_page), 100),  # Max 100 per page
        "offset": (max(1, page) - 1) * min(max(1, per_page), 100),
    }
