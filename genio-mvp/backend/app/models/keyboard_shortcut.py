"""
Keyboard shortcuts configuration model.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
import json

from sqlmodel import Field, SQLModel


# Default shortcuts configuration
DEFAULT_SHORTCUTS = {
    "navigation": {
        "next_item": {
            "key": "j",
            "modifiers": [],
            "description": "Next item",
            "enabled": True,
            "context": ["global", "list"]
        },
        "prev_item": {
            "key": "k",
            "modifiers": [],
            "description": "Previous item",
            "enabled": True,
            "context": ["global", "list"]
        },
        "go_to_top": {
            "key": "g",
            "double_tap": True,
            "modifiers": [],
            "description": "Go to top",
            "enabled": True,
            "context": ["global", "list"]
        },
        "go_to_bottom": {
            "key": "G",
            "modifiers": ["shift"],
            "description": "Go to bottom",
            "enabled": True,
            "context": ["global", "list"]
        },
        "page_down": {
            "key": "d",
            "modifiers": ["ctrl"],
            "description": "Page down",
            "enabled": True,
            "context": ["global", "reader"]
        },
        "page_up": {
            "key": "u",
            "modifiers": ["ctrl"],
            "description": "Page up",
            "enabled": True,
            "context": ["global", "reader"]
        },
        "search_focus": {
            "key": "/",
            "modifiers": [],
            "description": "Focus search",
            "enabled": True,
            "context": ["global"]
        },
        "go_to_feeds": {
            "key": "g",
            "then": "f",
            "description": "Go to feeds",
            "enabled": True,
            "context": ["global"]
        },
        "go_to_library": {
            "key": "g",
            "then": "l",
            "description": "Go to library",
            "enabled": True,
            "context": ["global"]
        },
        "go_to_briefs": {
            "key": "g",
            "then": "b",
            "description": "Go to briefs",
            "enabled": True,
            "context": ["global"]
        },
    },
    "actions": {
        "mark_read": {
            "key": "r",
            "modifiers": [],
            "description": "Mark as read/unread",
            "enabled": True,
            "context": ["list", "reader"]
        },
        "mark_favorite": {
            "key": "s",
            "modifiers": [],
            "description": "Toggle favorite",
            "enabled": True,
            "context": ["list", "reader"]
        },
        "archive": {
            "key": "e",
            "modifiers": [],
            "description": "Archive item",
            "enabled": True,
            "context": ["list", "reader"]
        },
        "open_original": {
            "key": "o",
            "modifiers": [],
            "description": "Open original URL",
            "enabled": True,
            "context": ["list", "reader"]
        },
        "open_reader": {
            "key": "Enter",
            "modifiers": [],
            "description": "Open in reader",
            "enabled": True,
            "context": ["list"]
        },
        "tag_item": {
            "key": "t",
            "modifiers": [],
            "description": "Tag item",
            "enabled": True,
            "context": ["list", "reader"]
        },
        "share_item": {
            "key": "S",
            "modifiers": ["shift"],
            "description": "Share item",
            "enabled": True,
            "context": ["list", "reader"]
        },
    },
    "reader": {
        "scroll_down": {
            "key": "j",
            "modifiers": [],
            "description": "Scroll down",
            "enabled": True,
            "context": ["reader"]
        },
        "scroll_up": {
            "key": "k",
            "modifiers": [],
            "description": "Scroll up",
            "enabled": True,
            "context": ["reader"]
        },
        "close_reader": {
            "key": "Escape",
            "modifiers": [],
            "description": "Close reader",
            "enabled": True,
            "context": ["reader"]
        },
        "toggle_fullscreen": {
            "key": "f",
            "modifiers": [],
            "description": "Toggle fullscreen",
            "enabled": True,
            "context": ["reader"]
        },
        "increase_font": {
            "key": "+",
            "modifiers": [],
            "description": "Increase font size",
            "enabled": True,
            "context": ["reader"]
        },
        "decrease_font": {
            "key": "-",
            "modifiers": [],
            "description": "Decrease font size",
            "enabled": True,
            "context": ["reader"]
        },
    },
    "application": {
        "new_feed": {
            "key": "n",
            "modifiers": ["ctrl"],
            "description": "New feed",
            "enabled": True,
            "context": ["global"]
        },
        "refresh": {
            "key": "r",
            "modifiers": ["ctrl"],
            "description": "Refresh",
            "enabled": True,
            "context": ["global"]
        },
        "help": {
            "key": "?",
            "modifiers": ["shift"],
            "description": "Show keyboard shortcuts",
            "enabled": True,
            "context": ["global"]
        },
        "settings": {
            "key": ",",
            "modifiers": [],
            "description": "Open settings",
            "enabled": True,
            "context": ["global"]
        },
    }
}


class KeyboardShortcutConfig(SQLModel, table=True):
    """User's keyboard shortcuts configuration."""
    __tablename__ = "keyboard_shortcuts"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True, unique=True)
    
    # Store complete shortcuts config as JSON
    config: str = Field(default="{}")
    
    # Version for migrations
    version: str = Field(default="1.0")
    
    # Whether Vim mode is enabled
    vim_mode_enabled: bool = Field(default=True)
    
    # Custom keybindings override
    custom_bindings: str = Field(default="{}")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_full_config(self) -> Dict[str, Any]:
        """Get merged config (defaults + custom overrides)."""
        try:
            custom = json.loads(self.custom_bindings) if self.custom_bindings else {}
        except json.JSONDecodeError:
            custom = {}
        
        if not self.vim_mode_enabled:
            # Return empty or minimal config if Vim mode disabled
            return {}
        
        # Start with defaults and apply custom overrides
        import copy
        config = copy.deepcopy(DEFAULT_SHORTCUTS)
        
        for category, shortcuts in custom.items():
            if category in config:
                config[category].update(shortcuts)
        
        return config
    
    def set_custom_binding(self, category: str, action: str, binding: Dict[str, Any]):
        """Set a custom keybinding."""
        try:
            custom = json.loads(self.custom_bindings) if self.custom_bindings else {}
        except json.JSONDecodeError:
            custom = {}
        
        if category not in custom:
            custom[category] = {}
        
        custom[category][action] = binding
        self.custom_bindings = json.dumps(custom)


# API Schemas
class ShortcutBinding(SQLModel):
    key: str
    modifiers: Optional[List[str]] = None
    then: Optional[str] = None  # For chord shortcuts (g then f)
    double_tap: Optional[bool] = None
    description: str
    enabled: bool = True
    context: List[str] = ["global"]


class ShortcutCategory(SQLModel):
    shortcuts: Dict[str, ShortcutBinding]


class ShortcutsResponse(SQLModel):
    navigation: Dict[str, Any]
    actions: Dict[str, Any]
    reader: Dict[str, Any]
    application: Dict[str, Any]


class UpdateShortcutRequest(SQLModel):
    key: Optional[str] = None
    modifiers: Optional[List[str]] = None
    enabled: Optional[bool] = None


class ShortcutConflict(SQLModel):
    category1: str
    action1: str
    category2: str
    action2: str
    conflicting_key: str


class ValidateShortcutsResponse(SQLModel):
    valid: bool
    conflicts: List[ShortcutConflict]


class ExportShortcutsResponse(SQLModel):
    version: str
    shortcuts: Dict[str, Any]
    exported_at: str


class ImportShortcutsRequest(SQLModel):
    version: str
    shortcuts: Dict[str, Any]
