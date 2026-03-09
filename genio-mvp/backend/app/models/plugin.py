"""
Plugin system models for extensibility.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlmodel import Field, SQLModel


class PluginType(str, Enum):
    """Types of plugins."""
    SOURCE = "source"  # Content source (RSS, API, etc.)
    PROCESSOR = "processor"  # Content processing
    EXPORTER = "exporter"  # Export destinations
    NOTIFIER = "notifier"  # Notification channels
    ANALYZER = "analyzer"  # AI/ML analysis
    INTEGRATION = "integration"  # Third-party integrations


class PluginStatus(str, Enum):
    """Plugin installation status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UPDATING = "updating"


class PluginManifest(SQLModel):
    """Plugin manifest schema."""
    id: str
    name: str
    version: str
    description: str
    author: str
    type: str  # PluginType
    
    # Requirements
    min_app_version: str
    max_app_version: Optional[str] = None
    dependencies: List[str] = []  # Other plugin IDs
    
    # Capabilities
    permissions: List[str] = []  # Required permissions
    settings_schema: Optional[Dict[str, Any]] = None  # JSON Schema for settings
    
    # Entry points
    entry_point: str  # Module path
    hooks: List[str] = []  # Event hooks the plugin listens to
    
    # UI
    has_settings_page: bool = False
    has_sidebar_item: bool = False
    icon: Optional[str] = None


class Plugin(SQLModel, table=True):
    """Installed plugin."""
    __tablename__ = "plugins"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    
    # Manifest data
    manifest_id: str = Field(index=True)
    name: str
    version: str
    description: Optional[str] = None
    author: str
    plugin_type: str
    
    # Source
    source: str  # "marketplace", "github", "local", "custom"
    source_url: Optional[str] = None
    
    # Status
    status: str = Field(default=PluginStatus.INACTIVE)
    error_message: Optional[str] = None
    
    # Settings (JSON)
    settings: str = Field(default="{}")
    
    # System
    is_system: bool = Field(default=False)  # Built-in plugins
    is_enabled: bool = Field(default=False)
    
    # Stats
    last_executed_at: Optional[datetime] = None
    execution_count: int = Field(default=0)
    error_count: int = Field(default=0)
    
    installed_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserPlugin(SQLModel, table=True):
    """User-specific plugin configuration."""
    __tablename__ = "user_plugins"
    
    user_id: str = Field(foreign_key="users.id", primary_key=True)
    plugin_id: str = Field(foreign_key="plugins.id", primary_key=True)
    
    # User settings override
    settings: str = Field(default="{}")
    is_enabled: bool = Field(default=True)
    
    # Position in UI
    sidebar_position: Optional[int] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PluginExecutionLog(SQLModel, table=True):
    """Log of plugin executions."""
    __tablename__ = "plugin_execution_logs"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    plugin_id: str = Field(foreign_key="plugins.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    
    # Execution details
    trigger: str  # "hook", "scheduled", "manual", "api"
    hook_name: Optional[str] = None
    
    # Input/Output
    input_data: str = Field(default="{}")  # JSON
    output_data: str = Field(default="{}")  # JSON
    
    # Result
    success: bool
    error_message: Optional[str] = None
    execution_time_ms: int
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PluginWebhook(SQLModel, table=True):
    """Webhook endpoints for plugins."""
    __tablename__ = "plugin_webhooks"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    plugin_id: str = Field(foreign_key="plugins.id", index=True)
    
    # Webhook config
    path: str  # URL path suffix
    secret: str  # For verification
    
    # Status
    is_active: bool = Field(default=True)
    last_called_at: Optional[datetime] = None
    call_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# API Schemas

class InstallPluginRequest(SQLModel):
    """Request to install a plugin."""
    source: str  # "marketplace", "url", "upload"
    manifest_url: Optional[str] = None
    file_data: Optional[str] = None  # Base64 encoded for uploads


class PluginResponse(SQLModel):
    """Plugin info response."""
    id: str
    manifest_id: str
    name: str
    version: str
    description: Optional[str]
    author: str
    plugin_type: str
    status: str
    is_enabled: bool
    is_system: bool
    installed_at: datetime
    

class UpdatePluginSettingsRequest(SQLModel):
    """Update plugin settings."""
    settings: Dict[str, Any]
    is_enabled: Optional[bool] = None


class PluginExecutionRequest(SQLModel):
    """Request to execute a plugin."""
    action: str
    parameters: Dict[str, Any] = {}


class PluginMarketplaceEntry(SQLModel):
    """Plugin from marketplace."""
    id: str
    name: str
    version: str
    description: str
    author: str
    type: str
    downloads: int
    rating: float
    icon_url: Optional[str]
    manifest_url: str


# Hook definitions
class PluginHook:
    """Available plugin hooks."""
    
    # Article lifecycle
    ARTICLE_FETCHED = "article:fetched"
    ARTICLE_EXTRACTED = "article:extracted"
    ARTICLE_EMBEDDED = "article:embedded"
    ARTICLE_READY = "article:ready"
    
    # User actions
    ARTICLE_READ = "article:read"
    ARTICLE_FAVORITED = "article:favorited"
    ARTICLE_TAGGED = "article:tagged"
    
    # Brief lifecycle
    BRIEF_GENERATING = "brief:generating"
    BRIEF_GENERATED = "brief:generated"
    BRIEF_SENT = "brief:sent"
    
    # System
    USER_REGISTERED = "user:registered"
    USER_LOGIN = "user:login"
    
    # Custom
    SCHEDULED = "scheduled"  # Cron-like scheduling
    CUSTOM = "custom"  # Plugin-specific
