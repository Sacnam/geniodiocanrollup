"""
API endpoints for two-factor authentication and SSO.
"""
import secrets
import json
import base64
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, and_

from app.db.database import get_session
from app.core.security import get_current_user, verify_password
from app.models.user import User
from app.models.two_factor import (
    TwoFactorAuth, TwoFactorChallenge, WebAuthnCredential, SSOConnection,
    TwoFAMethod, SetupTOTPResponse, VerifyTOTPRequest, Enable2FARequest,
    TwoFAChallengeRequest, TwoFAStatusResponse, Disable2FARequest
)
from app.utils.id_generator import generate_id
from app.core.encryption import encrypt_data, decrypt_data

# TOTP imports
try:
    import pyotp
    import qrcode
    from io import BytesIO
    TOTP_AVAILABLE = True
except ImportError:
    TOTP_AVAILABLE = False

router = APIRouter()


def generate_backup_codes(count: int = 10) -> List[str]:
    """Generate one-time backup codes."""
    return [
        ''.join(secrets.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(8))
        for _ in range(count)
    ]


# 2FA Setup

@router.get("/2fa/status", response_model=TwoFAStatusResponse)
async def get_2fa_status(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get current 2FA status."""
    tfa = session.exec(
        select(TwoFactorAuth).where(TwoFactorAuth.user_id == current_user.id)
    ).first()
    
    if not tfa:
        return TwoFAStatusResponse(
            enabled=False,
            methods=[],
            preferred_method=None,
            backup_codes_remaining=0,
            webauthn_keys=[]
        )
    
    methods = []
    if tfa.totp_enabled:
        methods.append("totp")
    if tfa.sms_enabled:
        methods.append("sms")
    if tfa.email_enabled:
        methods.append("email")
    if tfa.webauthn_enabled:
        methods.append("webauthn")
    
    # Get WebAuthn keys
    keys = session.exec(
        select(WebAuthnCredential).where(
            and_(
                WebAuthnCredential.user_id == current_user.id,
                WebAuthnCredential.is_active == True
            )
        )
    ).all()
    
    return TwoFAStatusResponse(
        enabled=len(methods) > 0,
        methods=methods,
        preferred_method=tfa.preferred_method if methods else None,
        backup_codes_remaining=len(json.loads(tfa.backup_codes)) - tfa.backup_codes_used,
        webauthn_keys=[
            {"id": k.id, "name": k.device_name, "type": k.device_type}
            for k in keys
        ]
    )


@router.post("/2fa/setup-totp")
async def setup_totp(
    password: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Start TOTP setup process."""
    if not TOTP_AVAILABLE:
        raise HTTPException(status_code=503, detail="TOTP not available")
    
    # Verify password
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Generate secret
    secret = pyotp.random_base32()
    
    # Create TOTP URI for QR code
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="Genio"
    )
    
    # Generate QR code
    qr = qrcode.make(uri)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Generate backup codes
    backup_codes = generate_backup_codes()
    
    # Store in challenge (temporary until verified)
    challenge = TwoFactorChallenge(
        id=generate_id("2fach"),
        user_id=current_user.id,
        challenge_type=TwoFAMethod.TOTP,
        challenge_token=generate_id("tkn"),
        challenge_data=json.dumps({
            "secret": secret,
            "backup_codes": backup_codes
        }),
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    session.add(challenge)
    session.commit()
    
    return {
        "challenge_token": challenge.challenge_token,
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "backup_codes": backup_codes  # Show once!
    }


@router.post("/2fa/verify-totp-setup")
async def verify_totp_setup(
    data: VerifyTOTPRequest,
    challenge_token: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Verify TOTP code and enable 2FA."""
    if not TOTP_AVAILABLE:
        raise HTTPException(status_code=503, detail="TOTP not available")
    
    # Get challenge
    challenge = session.exec(
        select(TwoFactorChallenge).where(
            and_(
                TwoFactorChallenge.challenge_token == challenge_token,
                TwoFactorChallenge.user_id == current_user.id,
                TwoFactorChallenge.expires_at > datetime.utcnow()
            )
        )
    ).first()
    
    if not challenge:
        raise HTTPException(status_code=400, detail="Invalid or expired challenge")
    
    # Parse stored data
    setup_data = json.loads(challenge.challenge_data)
    secret = setup_data["secret"]
    
    # Verify code
    totp = pyotp.TOTP(secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid code")
    
    # Enable TOTP
    tfa = session.exec(
        select(TwoFactorAuth).where(TwoFactorAuth.user_id == current_user.id)
    ).first()
    
    if not tfa:
        tfa = TwoFactorAuth(
            id=generate_id("2fa"),
            user_id=current_user.id
        )
    
    tfa.totp_secret = encrypt_data(secret)
    tfa.totp_enabled = True
    tfa.totp_verified = True
    tfa.backup_codes = json.dumps(setup_data["backup_codes"])
    tfa.enabled_at = datetime.utcnow()
    tfa.updated_at = datetime.utcnow()
    
    session.add(tfa)
    session.delete(challenge)  # Clean up challenge
    session.commit()
    
    return {"status": "enabled", "method": "totp"}


@router.post("/2fa/disable")
async def disable_2fa(
    data: Disable2FARequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Disable 2FA."""
    # Verify password
    if not verify_password(data.password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    tfa = session.exec(
        select(TwoFactorAuth).where(TwoFactorAuth.user_id == current_user.id)
    ).first()
    
    if not tfa:
        raise HTTPException(status_code=400, detail="2FA not enabled")
    
    # Disable all methods
    tfa.totp_enabled = False
    tfa.totp_secret = None
    tfa.sms_enabled = False
    tfa.sms_phone = None
    tfa.email_enabled = False
    tfa.backup_email = None
    tfa.webauthn_enabled = False
    tfa.backup_codes = "[]"
    tfa.updated_at = datetime.utcnow()
    
    # Deactivate WebAuthn keys
    keys = session.exec(
        select(WebAuthnCredential).where(WebAuthnCredential.user_id == current_user.id)
    ).all()
    for key in keys:
        key.is_active = False
        session.add(key)
    
    session.add(tfa)
    session.commit()
    
    return {"status": "disabled"}


# WebAuthn (Security Keys)

@router.post("/2fa/webauthn/begin-registration")
async def begin_webauthn_registration(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Start WebAuthn registration."""
    # This would integrate with a WebAuthn library
    # For now, return a placeholder
    return {
        "challenge": generate_id("webauthn"),
        "rp": {"name": "Genio", "id": "genio.ai"},
        "user": {
            "id": current_user.id,
            "name": current_user.email,
            "displayName": current_user.name or current_user.email
        },
        "pubKeyCredParams": [{"alg": -7, "type": "public-key"}]
    }


@router.post("/2fa/webauthn/verify-registration")
async def verify_webauthn_registration(
    credential: dict,
    device_name: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Complete WebAuthn registration."""
    # Store the credential
    webauthn_cred = WebAuthnCredential(
        id=generate_id("webauthn"),
        user_id=current_user.id,
        credential_id=credential.get("id"),
        public_key=credential.get("response", {}).get("publicKey", ""),
        device_name=device_name,
        device_type="security_key"
    )
    session.add(webauthn_cred)
    
    # Enable WebAuthn in 2FA settings
    tfa = session.exec(
        select(TwoFactorAuth).where(TwoFactorAuth.user_id == current_user.id)
    ).first()
    
    if not tfa:
        tfa = TwoFactorAuth(
            id=generate_id("2fa"),
            user_id=current_user.id
        )
    
    tfa.webauthn_enabled = True
    tfa.updated_at = datetime.utcnow()
    session.add(tfa)
    session.commit()
    
    return {"status": "registered", "device_id": webauthn_cred.id}


# SSO

@router.get("/auth/sso/providers")
async def list_sso_providers():
    """List available SSO providers."""
    return [
        {"id": "google", "name": "Google", "icon": "google"},
        {"id": "github", "name": "GitHub", "icon": "github"},
        {"id": "microsoft", "name": "Microsoft", "icon": "microsoft"},
    ]


@router.post("/auth/sso/{provider}/link")
async def link_sso_account(
    provider: str,
    access_token: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Link an SSO account to current user."""
    # Verify token with provider and get user info
    # This is a placeholder - would need actual OAuth implementation
    
    # Check if already linked
    existing = session.exec(
        select(SSOConnection).where(
            and_(
                SSOConnection.user_id == current_user.id,
                SSOConnection.provider == provider
            )
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Already linked")
    
    # Create connection
    connection = SSOConnection(
        id=generate_id("sso"),
        user_id=current_user.id,
        provider=provider,
        provider_user_id="placeholder",  # Would come from OAuth
        email=current_user.email
    )
    session.add(connection)
    session.commit()
    
    return {"status": "linked", "provider": provider}


@router.get("/auth/sso/connections")
async def list_sso_connections(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List linked SSO accounts."""
    connections = session.exec(
        select(SSOConnection).where(SSOConnection.user_id == current_user.id)
    ).all()
    
    return [
        {
            "id": c.id,
            "provider": c.provider,
            "email": c.email,
            "is_active": c.is_active,
            "last_login_at": c.last_login_at
        }
        for c in connections
    ]


@router.delete("/auth/sso/{connection_id}")
async def unlink_sso_account(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Unlink an SSO account."""
    connection = session.exec(
        select(SSOConnection).where(
            and_(
                SSOConnection.id == connection_id,
                SSOConnection.user_id == current_user.id
            )
        )
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    session.delete(connection)
    session.commit()
    
    return {"status": "unlinked"}
