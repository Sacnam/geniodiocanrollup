"""
Two-factor authentication models.
"""
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlmodel import Field, SQLModel


class TwoFAMethod(str, Enum):
    """2FA methods supported."""
    TOTP = "totp"  # Time-based OTP (Google Authenticator)
    SMS = "sms"    # SMS codes
    EMAIL = "email"  # Email codes
    WEBAUTHN = "webauthn"  # Security keys (YubiKey, etc.)
    BACKUP = "backup"  # Backup codes


class TwoFactorAuth(SQLModel, table=True):
    """User's 2FA configuration."""
    __tablename__ = "two_factor_auth"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True, unique=True)
    
    # TOTP settings
    totp_secret: Optional[str] = None  # Encrypted TOTP secret
    totp_enabled: bool = Field(default=False)
    totp_verified: bool = Field(default=False)
    
    # SMS settings
    sms_phone: Optional[str] = None
    sms_enabled: bool = Field(default=False)
    sms_verified: bool = Field(default=False)
    
    # Email settings (different from account email)
    backup_email: Optional[str] = None
    email_enabled: bool = Field(default=False)
    
    # WebAuthn/Security Keys
    webauthn_enabled: bool = Field(default=False)
    
    # Backup codes (hashed)
    backup_codes: str = Field(default="[]")  # JSON array of hashed codes
    backup_codes_used: int = Field(default=0)
    
    # Preferences
    preferred_method: str = Field(default=TwoFAMethod.TOTP)
    
    # Metadata
    enabled_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WebAuthnCredential(SQLModel, table=True):
    """WebAuthn security key credentials."""
    __tablename__ = "webauthn_credentials"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Credential data
    credential_id: str = Field(index=True)  # Base64URL encoded
    public_key: str  # Base64URL encoded
    sign_count: int = Field(default=0)
    
    # Device info
    device_name: Optional[str] = None
    device_type: Optional[str] = None  # "security_key", "platform", "hybrid"
    
    # Status
    is_active: bool = Field(default=True)
    last_used_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TwoFactorChallenge(SQLModel, table=True):
    """Temporary 2FA challenges during login."""
    __tablename__ = "two_factor_challenges"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Challenge data
    challenge_type: str  # totp, sms, email, webauthn
    challenge_token: str = Field(index=True, unique=True)
    
    # For TOTP/WebAuthn - stores the challenge
    challenge_data: Optional[str] = None
    
    # For SMS/Email - stores the code
    code: Optional[str] = None
    code_attempts: int = Field(default=0)
    
    # Expiration
    expires_at: datetime
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# API Schemas
class SetupTOTPRequest(SQLModel):
    """Request to setup TOTP."""
    password: str  # Current password for verification


class SetupTOTPResponse(SQLModel):
    """Response with TOTP setup data."""
    secret: str  # The TOTP secret
    qr_code_uri: str  # QR code for scanning
    backup_codes: List[str]  # One-time backup codes


class VerifyTOTPRequest(SQLModel):
    """Verify TOTP during setup."""
    code: str  # 6-digit code from authenticator


class Enable2FARequest(SQLModel):
    """Enable 2FA with method."""
    method: str  # totp, sms, email
    phone: Optional[str] = None  # For SMS
    backup_email: Optional[str] = None  # For email


class TwoFAChallengeRequest(SQLModel):
    """Submit 2FA code during login."""
    challenge_token: str
    code: str  # TOTP/SMS/Email code


class TwoFAStatusResponse(SQLModel):
    """Current 2FA status."""
    enabled: bool
    methods: List[str]
    preferred_method: Optional[str]
    backup_codes_remaining: int
    webauthn_keys: List[Dict]


class Disable2FARequest(SQLModel):
    """Disable 2FA."""
    password: str
    reason: Optional[str] = None


class SSOProvider(str, Enum):
    """Supported SSO providers."""
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    OKTA = "okta"
    SAML = "saml"


class SSOConnection(SQLModel, table=True):
    """SSO connection for a user."""
    __tablename__ = "sso_connections"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    provider: str  # SSOProvider
    provider_user_id: str  # User ID from provider
    
    # Tokens (encrypted)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    
    # Profile data from provider
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    is_active: bool = Field(default=True)
    last_login_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SSOSettings(SQLModel, table=True):
    """SSO settings for teams/organizations."""
    __tablename__ = "sso_settings"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    team_id: Optional[str] = Field(foreign_key="teams.id", nullable=True)
    
    provider: str
    
    # Configuration (encrypted)
    client_id: str
    client_secret: str
    
    # SAML specific
    saml_metadata_url: Optional[str] = None
    saml_certificate: Optional[str] = None
    
    # Settings
    enforce_sso: bool = Field(default=False)  # Require SSO login
    auto_provision: bool = Field(default=True)  # Auto-create accounts
    
    is_active: bool = Field(default=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Import List from typing
from typing import List, Dict
