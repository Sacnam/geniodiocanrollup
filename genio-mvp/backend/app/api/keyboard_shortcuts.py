"""
API endpoints for keyboard shortcuts configuration.
"""
import json
from datetime import datetime
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, and_

from app.db.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.keyboard_shortcut import (
    KeyboardShortcutConfig, DEFAULT_SHORTCUTS,
    ShortcutsResponse, UpdateShortcutRequest,
    ValidateShortcutsResponse, ShortcutConflict,
    ExportShortcutsResponse, ImportShortcutsRequest
)
from app.utils.id_generator import generate_id

router = APIRouter()


def get_or_create_config(session: Session, user_id: str) -> KeyboardShortcutConfig:
    """Get or create shortcut config for user."""
    config = session.exec(
        select(KeyboardShortcutConfig).where(
            KeyboardShortcutConfig.user_id == user_id
        )
    ).first()
    
    if not config:
        config = KeyboardShortcutConfig(
            id=generate_id("kbscfg"),
            user_id=user_id,
            config=json.dumps(DEFAULT_SHORTCUTS),
            vim_mode_enabled=True,
            custom_bindings="{}"
        )
        session.add(config)
        session.commit()
        session.refresh(config)
    
    return config


def check_conflicts(shortcuts: Dict[str, Any]) -> List[ShortcutConflict]:
    """Check for conflicting keybindings."""
    conflicts = []
    seen: Dict[str, tuple] = {}  # key -> (category, action)
    
    for category, actions in shortcuts.items():
        for action, binding in actions.items():
            if not binding.get("enabled", True):
                continue
            
            # Build key representation
            key_parts = []
            if binding.get("modifiers"):
                key_parts.extend(sorted(binding["modifiers"]))
            key_parts.append(binding.get("key", ""))
            key_repr = "+".join(key_parts)
            
            if key_repr in seen:
                other_cat, other_act = seen[key_repr]
                conflicts.append(ShortcutConflict(
                    category1=other_cat,
                    action1=other_act,
                    category2=category,
                    action2=action,
                    conflicting_key=key_repr
                ))
            else:
                seen[key_repr] = (category, action)
    
    return conflicts


@router.get("", response_model=ShortcutsResponse)
async def get_shortcuts(
    context: str = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get user's keyboard shortcuts configuration."""
    config = get_or_create_config(session, current_user.id)
    full_config = config.get_full_config()
    
    # Filter by context if specified
    if context:
        filtered = {}
        for category, actions in full_config.items():
            filtered[category] = {
                name: binding for name, binding in actions.items()
                if context in binding.get("context", ["global"])
            }
        return filtered
    
    return full_config


@router.put("/{category}/{action}")
async def update_shortcut(
    category: str,
    action: str,
    data: UpdateShortcutRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a specific keyboard shortcut."""
    config = get_or_create_config(session, current_user.id)
    
    # Get current binding
    full_config = config.get_full_config()
    
    if category not in full_config or action not in full_config[category]:
        raise HTTPException(status_code=404, detail="Shortcut not found")
    
    binding = full_config[category][action]
    
    # Apply updates
    if data.key is not None:
        binding["key"] = data.key
    if data.modifiers is not None:
        binding["modifiers"] = data.modifiers
    if data.enabled is not None:
        binding["enabled"] = data.enabled
    
    # Save to custom bindings
    config.set_custom_binding(category, action, binding)
    config.updated_at = datetime.utcnow()
    
    session.add(config)
    session.commit()
    
    return binding


@router.post("/reset")
async def reset_shortcuts(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Reset all shortcuts to defaults."""
    config = session.exec(
        select(KeyboardShortcutConfig).where(
            KeyboardShortcutConfig.user_id == current_user.id
        )
    ).first()
    
    if config:
        config.custom_bindings = "{}"
        config.vim_mode_enabled = True
        config.updated_at = datetime.utcnow()
        session.add(config)
        session.commit()
    
    return {"status": "reset", "shortcuts": DEFAULT_SHORTCUTS}


@router.post("/validate", response_model=ValidateShortcutsResponse)
async def validate_shortcuts(
    shortcuts: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Validate shortcuts for conflicts."""
    conflicts = check_conflicts(shortcuts)
    
    return ValidateShortcutsResponse(
        valid=len(conflicts) == 0,
        conflicts=conflicts
    )


@router.get("/export", response_model=ExportShortcutsResponse)
async def export_shortcuts(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Export shortcuts configuration."""
    config = get_or_create_config(session, current_user.id)
    
    return ExportShortcutsResponse(
        version=config.version,
        shortcuts=config.get_full_config(),
        exported_at=datetime.utcnow().isoformat()
    )


@router.post("/import")
async def import_shortcuts(
    data: ImportShortcutsRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Import shortcuts configuration."""
    # Validate for conflicts
    conflicts = check_conflicts(data.shortcuts)
    if conflicts:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Import contains conflicts",
                "conflicts": [c.dict() for c in conflicts]
            }
        )
    
    config = get_or_create_config(session, current_user.id)
    config.custom_bindings = json.dumps(data.shortcuts)
    config.version = data.version
    config.updated_at = datetime.utcnow()
    
    session.add(config)
    session.commit()
    
    return {"status": "imported", "shortcuts": config.get_full_config()}


@router.get("/cheatsheet")
async def get_cheatsheet(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get formatted cheatsheet for display."""
    config = get_or_create_config(session, current_user.id)
    full_config = config.get_full_config()
    
    cheatsheet = []
    
    for category, actions in full_config.items():
        shortcuts = []
        for name, binding in actions.items():
            if not binding.get("enabled", True):
                continue
            
            # Format key combination
            key_display = binding.get("key", "")
            if binding.get("modifiers"):
                mod_display = " + ".join(binding["modifiers"])
                key_display = f"{mod_display} + {key_display}"
            
            if binding.get("double_tap"):
                key_display = f"{key_display} (double-tap)"
            
            if binding.get("then"):
                key_display = f"{key_display}, {binding['then']}"
            
            shortcuts.append({
                "action": name,
                "key": key_display,
                "description": binding.get("description", "")
            })
        
        cheatsheet.append({
            "category": category,
            "shortcuts": shortcuts
        })
    
    return cheatsheet


@router.post("/toggle-vim-mode")
async def toggle_vim_mode(
    enabled: bool,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Enable or disable Vim mode."""
    config = get_or_create_config(session, current_user.id)
    config.vim_mode_enabled = enabled
    config.updated_at = datetime.utcnow()
    
    session.add(config)
    session.commit()
    
    return {"vim_mode_enabled": enabled}
