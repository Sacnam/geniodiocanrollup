"""
WebSocket Real-time Updates
Provides live notifications and updates to clients
"""
import asyncio
import json
from typing import Dict, List, Optional, Set
from datetime import datetime

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.auth import get_current_user_ws
from app.models.user import User

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        # user_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Global connections (for broadcasts)
        self.global_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.global_connections.add(websocket)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        self.global_connections.discard(websocket)
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections of a user."""
        if user_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.active_connections[user_id].discard(conn)
    
    async def broadcast(self, message: dict):
        """Broadcast to all connected clients."""
        disconnected = set()
        for connection in self.global_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        for conn in disconnected:
            self.global_connections.discard(conn)
    
    async def send_to_users(self, user_ids: List[str], message: dict):
        """Send message to multiple users."""
        for user_id in user_ids:
            await self.send_to_user(user_id, message)
    
    def get_user_connections(self, user_id: str) -> int:
        """Get number of active connections for user."""
        return len(self.active_connections.get(user_id, set()))
    
    def get_total_connections(self) -> int:
        """Get total number of connections."""
        return len(self.global_connections)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time updates.
    
    Authentication: Pass JWT token in query param ?token=xxx
    """
    # Authenticate
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        user = await get_current_user_ws(token, db)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await manager.connect(websocket, user.id)
    
    try:
        while True:
            # Receive and handle messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_message(websocket, user, message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, user.id)


async def handle_message(websocket: WebSocket, user: User, message: dict):
    """Handle incoming WebSocket message."""
    msg_type = message.get("type")
    
    if msg_type == "ping":
        await websocket.send_json({"type": "pong"})
    
    elif msg_type == "subscribe":
        # Subscribe to specific events
        channel = message.get("channel")
        await websocket.send_json({
            "type": "subscribed",
            "channel": channel
        })
    
    elif msg_type == "mark_read":
        # Mark article/notification as read
        item_id = message.get("item_id")
        item_type = message.get("item_type")
        # Would update database
        await websocket.send_json({
            "type": "marked_read",
            "item_id": item_id
        })
    
    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {msg_type}"
        })


# ==================== NOTIFICATION HELPERS ====================

async def notify_article_ready(user_id: str, article_id: str, title: str):
    """Notify user that an article has been processed."""
    await manager.send_to_user(user_id, {
        "type": "article_ready",
        "article_id": article_id,
        "title": title,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_brief_delivered(user_id: str, brief_id: str, title: str):
    """Notify user of new brief delivery."""
    await manager.send_to_user(user_id, {
        "type": "brief_delivered",
        "brief_id": brief_id,
        "title": title,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_document_processed(user_id: str, document_id: str, title: str):
    """Notify user that document processing is complete."""
    await manager.send_to_user(user_id, {
        "type": "document_processed",
        "document_id": document_id,
        "title": title,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_scout_insight(user_id: str, scout_id: str, insight: str):
    """Notify user of new scout insight."""
    await manager.send_to_user(user_id, {
        "type": "scout_insight",
        "scout_id": scout_id,
        "insight": insight,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_system_message(message: str, level: str = "info"):
    """Broadcast system message to all users."""
    await manager.broadcast({
        "type": "system_message",
        "message": message,
        "level": level,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_high_priority(user_ids: List[str], title: str, body: str):
    """Send high priority notification to specific users."""
    await manager.send_to_users(user_ids, {
        "type": "high_priority",
        "title": title,
        "body": body,
        "timestamp": datetime.utcnow().isoformat()
    })


# ==================== ADMIN ENDPOINTS ====================

@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "total_connections": manager.get_total_connections(),
        "active_users": len(manager.active_connections),
        "connections_per_user": {
            user_id: len(connections)
            for user_id, connections in manager.active_connections.items()
        }
    }
