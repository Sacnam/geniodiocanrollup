"""
Application configuration with pydantic-settings.

SECURITY NOTE:
    - JWT_SECRET_KEY is REQUIRED in production (no default)
    - API keys should be set via environment variables
    - Never commit actual secrets to version control
"""
import os
import secrets
from typing import List, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment.
    
    Required in Production:
        - JWT_SECRET_KEY: Must be set via environment variable
        - DATABASE_URL: PostgreSQL connection string
        - OPENAI_API_KEY: Required for AI features
        - GEMINI_API_KEY: Required for AI features
    
    Optional:
        - SENDGRID_API_KEY: For email delivery
        - STRIPE_*: For billing features
    """
    
    # App
    APP_NAME: str = "Genio Knowledge OS"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql://genio:genio_password@localhost:5432/genio"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "genio_articles"
    
    # AI Providers (Optional - validated at startup if features require them)
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LITELLM_API_BASE: Optional[str] = None
    
    # Email
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "briefs@genio.ai"
    
    # JWT Authentication
    # SECURITY: No default value in production - must be set via environment
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Budget
    MONTHLY_AI_BUDGET_USD: float = 3.0
    
    # Stripe (Optional - for billing)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_production_settings(self) -> 'Settings':
        """Validate that required settings are present in production."""
        # In production mode, JWT_SECRET_KEY is mandatory
        if not self.DEBUG and not self.JWT_SECRET_KEY:
            raise ValueError(
                "JWT_SECRET_KEY environment variable is REQUIRED in production. "
                "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        
        # Warn if using development defaults in production
        if not self.DEBUG:
            if "localhost" in self.DATABASE_URL:
                import warnings
                warnings.warn(
                    "DATABASE_URL points to localhost in production mode. "
                    "This may indicate a configuration error."
                )
        
        return self
    
    def get_jwt_secret_key(self) -> str:
        """Get JWT secret key, generating a random one for development if not set."""
        if self.JWT_SECRET_KEY:
            return self.JWT_SECRET_KEY
        
        if self.DEBUG:
            # Generate a random key for development only
            if not hasattr(self, '_dev_jwt_key'):
                self._dev_jwt_key = secrets.token_urlsafe(32)
            return self._dev_jwt_key
        
        # This should never happen due to model_validator, but just in case
        raise ValueError(
            "JWT_SECRET_KEY is not set. Set it via environment variable or enable DEBUG mode."
        )
    
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        """Alias for JWT_ACCESS_TOKEN_EXPIRE_MINUTES for backward compatibility."""
        return self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    
    @property
    def REFRESH_TOKEN_EXPIRE_DAYS(self) -> int:
        """Alias for JWT_REFRESH_TOKEN_EXPIRE_DAYS for backward compatibility."""
        return self.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars


# Create settings instance
# This will raise an error in production if required settings are missing
def create_settings() -> Settings:
    """Create settings instance with proper error handling."""
    try:
        return Settings()
    except ValueError as e:
        import sys
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)


settings = create_settings()
