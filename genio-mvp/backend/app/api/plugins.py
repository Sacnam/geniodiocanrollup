"""
API endpoints for plugin system.
"""
import json
import base64
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select, and_

from app.db.database import get_session
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.models.plugin import (
    Plugin, UserPlugin, PluginExecutionLog, PluginManifest,
    PluginType, PluginStatus,
    InstallPluginRequest, PluginResponse, UpdatePluginSettingsRequest,
    PluginExecutionRequest, PluginMarketplaceEntry
)
from app.utils.id_generator import generate_id

router = APIRouter()


# Marketplace (mock data - would be fetched from actual marketplace)
MARKETPLACE_PLUGINS = [
    PluginMarketplaceEntry(
        id="slack-notifier",
        name="Slack Notifications",
        version="1.0.0",
        description="Send Daily Briefs and alerts to Slack channels",
        author="Genio Team",
        type="notifier",
        downloads=1250,
        rating=4.5,
        icon_url="/icons/slack.svg",
        manifest_url="https://plugins.genio.ai/slack/manifest.json"
    ),
    PluginMarketplaceEntry(
        id="discord-webhook",
        name="Discord Integration",
        version="1.2.0",
        description="Share articles and receive notifications in Discord",
        author="Community",
        type="integration",
        downloads=890,
        rating=4.2,
        icon_url="/icons/discord.svg",
        manifest_url="https://plugins.genio.ai/discord/manifest.json"
    ),
    PluginMarketplaceEntry(
        id="twitter-source",
        name="Twitter/X Lists",
        version="2.0.0",
        description="Follow Twitter lists as RSS feeds",
        author="Genio Team",
        type="source",
        downloads=2100,
        rating=4.0,
        icon_url="/icons/twitter.svg",
        manifest_url="https://plugins.genio.ai/twitter/manifest.json"
    ),
    PluginMarketplaceEntry(
        id="arxiv-enhanced",
        name="arXiv Enhanced",
        version="1.5.0",
        description="Advanced arXiv filtering with AI summarization",
        author="Research Tools Inc",
        type="source",
        downloads=3400,
        rating=4.8,
        icon_url="/icons/arxiv.svg",
        manifest_url="https://plugins.genio.ai/arxiv/manifest.json"
    ),
    PluginMarketplaceEntry(
        id="pdf-export",
        name="PDF Export Pro",
        version="1.0.0",
        description="Export articles and briefs as formatted PDFs",
        author="Genio Team",
        type="exporter",
        downloads=560,
        rating=4.3,
        icon_url="/icons/pdf.svg",
        manifest_url="https://plugins.genio.ai/pdf-export/manifest.json"
    ),
    PluginMarketplaceEntry(
        id="sentiment-analyzer",
        name="Sentiment Analysis",
        version="1.1.0",
        description="AI-powered sentiment analysis for articles",
        author="AI Labs",
        type="analyzer",
        downloads=780,
        rating=4.1,
        icon_url="/icons/sentiment.svg",
        manifest_url="https://plugins.genio.ai/sentiment/manifest.json"
    ),
]


@router.get("/marketplace", response_model=List[PluginMarketplaceEntry])
async def list_marketplace_plugins(
    plugin_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List available plugins from marketplace."""
    plugins = MARKETPLACE_PLUGINS
    
    # Filter by type
    if plugin_type:
        plugins = [p for p in plugins if p.type == plugin_type]
    
    # Filter by search
    if search:
        search_lower = search.lower()
        plugins = [
            p for p in plugins
            if search_lower in p.name.lower()
            or search_lower in p.description.lower()
        ]
    
    return plugins


@router.get("/marketplace/{plugin_id}")
async def get_marketplace_plugin(
    plugin_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get details of a marketplace plugin."""
    plugin = next((p for p in MARKETPLACE_PLUGINS if p.id == plugin_id), None)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    return plugin


@router.post("/install")
async def install_plugin(
    data: InstallPluginRequest,
    current_user: User = Depends(require_admin),  # Only admins can install
    session: Session = Depends(get_session)
):
    """Install a plugin."""
    # Check if already installed
    existing = session.exec(
        select(Plugin).where(Plugin.manifest_id == data.manifest_id if hasattr(data, 'manifest_id') else False)
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Plugin already installed")
    
    # In a real implementation, would:
    # 1. Download/fetch the plugin code
    # 2. Verify signature
    # 3. Validate manifest
    # 4. Extract to plugins directory
    # 5. Run installation hooks
    
    # For demo, create from marketplace data
    marketplace_plugin = next(
        (p for p in MARKETPLACE_PLUGINS if p.manifest_url == data.manifest_url),
        None
    )
    
    if not marketplace_plugin:
        raise HTTPException(status_code=404, detail="Plugin not found in marketplace")
    
    plugin = Plugin(
        id=generate_id("plugin"),
        manifest_id=marketplace_plugin.id,
        name=marketplace_plugin.name,
        version=marketplace_plugin.version,
        description=marketplace_plugin.description,
        author=marketplace_plugin.author,
        plugin_type=marketplace_plugin.type,
        source="marketplace",
        source_url=marketplace_plugin.manifest_url,
        status=PluginStatus.INACTIVE,
        settings="{}",
        is_system=False,
        is_enabled=False
    )
    
    session.add(plugin)
    session.commit()
    session.refresh(plugin)
    
    return {
        "status": "installed",
        "plugin_id": plugin.id,
        "message": f"Plugin '{plugin.name}' installed successfully. Enable it to start using."
    }


@router.get("/installed", response_model=List[PluginResponse])
async def list_installed_plugins(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List installed plugins."""
    plugins = session.exec(
        select(Plugin).order_by(Plugin.installed_at.desc())
    ).all()
    
    # Get user-specific settings
    user_plugins = session.exec(
        select(UserPlugin).where(UserPlugin.user_id == current_user.id)
    ).all()
    user_plugin_map = {up.plugin_id: up for up in user_plugins}
    
    result = []
    for plugin in plugins:
        user_plugin = user_plugin_map.get(plugin.id)
        
        result.append(PluginResponse(
            id=plugin.id,
            manifest_id=plugin.manifest_id,
            name=plugin.name,
            version=plugin.version,
            description=plugin.description,
            author=plugin.author,
            plugin_type=plugin.plugin_type,
            status=plugin.status,
            is_enabled=user_plugin.is_enabled if user_plugin else plugin.is_enabled,
            is_system=plugin.is_system,
            installed_at=plugin.installed_at
        ))
    
    return result


@router.get("/installed/{plugin_id}")
async def get_plugin_details(
    plugin_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get detailed plugin info."""
    plugin = session.get(Plugin, plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # Get user settings
    user_plugin = session.exec(
        select(UserPlugin).where(
            and_(
                UserPlugin.plugin_id == plugin_id,
                UserPlugin.user_id == current_user.id
            )
        )
    ).first()
    
    return {
        **plugin.dict(),
        "settings": json.loads(plugin.settings),
        "user_settings": json.loads(user_plugin.settings) if user_plugin else {},
        "user_enabled": user_plugin.is_enabled if user_plugin else plugin.is_enabled,
        "execution_count": plugin.execution_count,
        "error_count": plugin.error_count,
        "last_executed_at": plugin.last_executed_at
    }


@router.post("/installed/{plugin_id}/enable")
async def enable_plugin(
    plugin_id: str,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """Enable a plugin."""
    plugin = session.get(Plugin, plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # In real implementation, would:
    # 1. Load the plugin module
    # 2. Run initialization
    # 3. Register hooks
    
    plugin.is_enabled = True
    plugin.status = PluginStatus.ACTIVE
    plugin.updated_at = datetime.utcnow()
    session.add(plugin)
    session.commit()
    
    return {"status": "enabled"}


@router.post("/installed/{plugin_id}/disable")
async def disable_plugin(
    plugin_id: str,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """Disable a plugin."""
    plugin = session.get(Plugin, plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin.is_enabled = False
    plugin.status = PluginStatus.INACTIVE
    plugin.updated_at = datetime.utcnow()
    session.add(plugin)
    session.commit()
    
    return {"status": "disabled"}


@router.put("/installed/{plugin_id}/settings")
async def update_plugin_settings(
    plugin_id: str,
    data: UpdatePluginSettingsRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update plugin settings."""
    plugin = session.get(Plugin, plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # Get or create user plugin config
    user_plugin = session.exec(
        select(UserPlugin).where(
            and_(
                UserPlugin.plugin_id == plugin_id,
                UserPlugin.user_id == current_user.id
            )
        )
    ).first()
    
    if not user_plugin:
        user_plugin = UserPlugin(
            user_id=current_user.id,
            plugin_id=plugin_id
        )
    
    if data.settings is not None:
        user_plugin.settings = json.dumps(data.settings)
    
    if data.is_enabled is not None:
        user_plugin.is_enabled = data.is_enabled
    
    user_plugin.updated_at = datetime.utcnow()
    session.add(user_plugin)
    session.commit()
    
    return {"status": "updated"}


@router.post("/installed/{plugin_id}/execute")
async def execute_plugin(
    plugin_id: str,
    data: PluginExecutionRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Execute a plugin action."""
    plugin = session.get(Plugin, plugin_id)
    if not plugin or not plugin.is_enabled:
        raise HTTPException(status_code=404, detail="Plugin not found or disabled")
    
    # Check user has access
    user_plugin = session.exec(
        select(UserPlugin).where(
            and_(
                UserPlugin.plugin_id == plugin_id,
                UserPlugin.user_id == current_user.id,
                UserPlugin.is_enabled == True
            )
        )
    ).first()
    
    if not user_plugin and not plugin.is_system:
        raise HTTPException(status_code=403, detail="Plugin not enabled for user")
    
    start_time = datetime.utcnow()
    
    # In real implementation, would:
    # 1. Load and execute the plugin
    # 2. Pass parameters
    # 3. Capture output
    
    # Mock execution
    success = True
    output = {"result": "mock_execution", "action": data.action}
    error = None
    
    execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    
    # Log execution
    log = PluginExecutionLog(
        id=generate_id("plog"),
        plugin_id=plugin_id,
        user_id=current_user.id,
        trigger="api",
        input_data=json.dumps(data.parameters),
        output_data=json.dumps(output),
        success=success,
        error_message=error,
        execution_time_ms=execution_time
    )
    session.add(log)
    
    # Update plugin stats
    plugin.execution_count += 1
    plugin.last_executed_at = datetime.utcnow()
    if not success:
        plugin.error_count += 1
        plugin.status = PluginStatus.ERROR
        plugin.error_message = error
    session.add(plugin)
    
    session.commit()
    
    if not success:
        raise HTTPException(status_code=500, detail=error)
    
    return output


@router.delete("/installed/{plugin_id}")
async def uninstall_plugin(
    plugin_id: str,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """Uninstall a plugin."""
    plugin = session.get(Plugin, plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    if plugin.is_system:
        raise HTTPException(status_code=403, detail="Cannot uninstall system plugins")
    
    # Delete user configs
    user_plugins = session.exec(
        select(UserPlugin).where(UserPlugin.plugin_id == plugin_id)
    ).all()
    for up in user_plugins:
        session.delete(up)
    
    # Delete logs
    logs = session.exec(
        select(PluginExecutionLog).where(PluginExecutionLog.plugin_id == plugin_id)
    ).all()
    for log in logs:
        session.delete(log)
    
    # Delete plugin
    session.delete(plugin)
    session.commit()
    
    return {"status": "uninstalled"}


@router.get("/hooks")
async def list_available_hooks(
    current_user: User = Depends(get_current_user)
):
    """List available plugin hooks."""
    from app.models.plugin import PluginHook
    
    return {
        "article": {
            "fetched": PluginHook.ARTICLE_FETCHED,
            "extracted": PluginHook.ARTICLE_EXTRACTED,
            "embedded": PluginHook.ARTICLE_EMBEDDED,
            "ready": PluginHook.ARTICLE_READY,
            "read": PluginHook.ARTICLE_READ,
            "favorited": PluginHook.ARTICLE_FAVORITED,
            "tagged": PluginHook.ARTICLE_TAGGED,
        },
        "brief": {
            "generating": PluginHook.BRIEF_GENERATING,
            "generated": PluginHook.BRIEF_GENERATED,
            "sent": PluginHook.BRIEF_SENT,
        },
        "user": {
            "registered": PluginHook.USER_REGISTERED,
            "login": PluginHook.USER_LOGIN,
        },
        "system": {
            "scheduled": PluginHook.SCHEDULED,
            "custom": PluginHook.CUSTOM,
        }
    }


@router.get("/types")
async def list_plugin_types(
    current_user: User = Depends(get_current_user)
):
    """List available plugin types."""
    return [
        {"id": "source", "name": "Content Source", "description": "Add new content sources (RSS, APIs, etc.)"},
        {"id": "processor", "name": "Content Processor", "description": "Process and transform content"},
        {"id": "exporter", "name": "Exporter", "description": "Export to external destinations"},
        {"id": "notifier", "name": "Notifier", "description": "Send notifications to external services"},
        {"id": "analyzer", "name": "Analyzer", "description": "AI/ML analysis and insights"},
        {"id": "integration", "name": "Integration", "description": "Third-party integrations"},
    ]
