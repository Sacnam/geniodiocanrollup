"""
Authentication utilities for Genio Knowledge OS.

This module provides:
    - Password hashing and verification
    - JWT token creation and validation
    - FastAPI dependencies for user authentication

SECURITY FIX (ARCH-001):
    - get_current_user now uses dependency injection for DB session
    - No more manual SessionLocal() creation (anti-pattern fixed)
"""
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel import Session

from app.core.config import settings

# Import get_session for dependency injection
# Using TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from app.models.user import User


def _get_session():
    """Lazy import of get_session to avoid circular imports."""
    from app.core.database import get_session
    return get_session

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT setup
security = HTTPBearer()


class TokenData(BaseModel):
    """Data extracted from a JWT token."""
    user_id: Optional[str] = None
    email: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def create_access_token(user_id: str, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.
    
    Args:
        user_id: The user's unique identifier
        email: The user's email address
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "type": "access",
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.get_jwt_secret_key(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token.
    
    Args:
        user_id: The user's unique identifier
        
    Returns:
        Encoded JWT refresh token string
    """
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.get_jwt_secret_key(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token.
    
    Args:
        token: The JWT token string
        
    Returns:
        TokenData with user_id and email
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.get_jwt_secret_key(),
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None:
            raise JWTError()
        
        return TokenData(user_id=user_id, email=email)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Extract user ID from JWT token.
    
    Use this when you only need the user ID and don't need to query the database.
    
    Args:
        credentials: HTTP Bearer credentials from FastAPI
        
    Returns:
        User ID string
        
    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    token_data = decode_token(token)
    
    if token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data.user_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(_get_session),
) -> "User":
    """Get the current authenticated user from JWT token.
    
    ARCHITECTURE FIX (ARCH-001):
        This function now uses FastAPI's dependency injection for the database
        session instead of manually creating SessionLocal(). This ensures:
        - Proper connection pooling
        - Consistent transaction management
        - Easier testing with mock sessions
        - No connection leaks
    
    Args:
        credentials: HTTP Bearer credentials from FastAPI
        db: Database session from dependency injection
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    from app.models.user import User
    
    token = credentials.credentials
    token_data = decode_token(token)
    
    if token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return user


# Legacy function for backward compatibility
# DEPRECATED: Use get_current_user with DI instead
async def get_current_user_legacy(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> "User":
    """Legacy version that creates its own DB session.
    
    DEPRECATED: This function is kept for backward compatibility during migration.
    Use get_current_user instead, which uses proper dependency injection.
    
    This function will be removed in a future version.
    """
    from sqlmodel import Session
    from app.core.database import SessionLocal
    from app.models.user import User
    
    token = credentials.credentials
    token_data = decode_token(token)
    
    if token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )
        return user
    finally:
        db.close()
