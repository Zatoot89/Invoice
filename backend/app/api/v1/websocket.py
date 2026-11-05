"""
InvoiceFlow Pro - WebSocket API Routes
"""
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from typing import Optional

from app.services.websocket_service import (
    connection_manager,
    notification_service,
    authenticate_websocket,
    handle_websocket_message
)
from app.core.deps import get_current_user
from app.models.user import User
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time notifications
    
    Usage:
    ws://localhost:8000/api/v1/ws/ws?token=your_jwt_token
    """
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return
    
    try:
        # Authenticate user
        user_id = await authenticate_websocket(websocket, token)
        
        # Connect to WebSocket
        await connection_manager.connect(websocket, user_id, {
            "token": token[:10] + "...",  # Store truncated token for logging
        })
        
        logger.info(f"WebSocket connected: User {user_id}")
        
        # Handle messages
        try:
            while True:
                # Wait for message from client
                data = await websocket.receive_text()
                
                try:
                    message_data = json.loads(data)
                    await handle_websocket_message(websocket, message_data)
                except json.JSONDecodeError:
                    await connection_manager.send_personal_message({
                        "type": "error",
                        "message": "Invalid JSON message"
                    }, websocket)
                except Exception as e:
                    logger.error(f"Message handling error: {str(e)}")
                    await connection_manager.send_personal_message({
                        "type": "error",
                        "message": "Message processing failed"
                    }, websocket)
        
        except WebSocketDisconnect:
            connection_manager.disconnect(websocket)
            logger.info(f"WebSocket disconnected: User {user_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


@router.get("/connections")
async def get_connection_stats(current_user: User = Depends(get_current_user)):
    """Get WebSocket connection statistics (admin only)"""
    if current_user.role != "admin":
        return {"error": "Admin access required"}
    
    stats = await notification_service.get_connection_stats()
    return stats


@router.post("/notify/test")
async def send_test_notification(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Send a test notification (for testing purposes)"""
    target_user_id = user_id or current_user.id
    
    await notification_service.notify_user_activity(target_user_id, {
        "title": "Test Notification",
        "message": "This is a test notification from the InvoiceFlow Pro system",
        "type": "test",
        "sender": current_user.full_name
    })
    
    return {
        "message": f"Test notification sent to user {target_user_id}",
        "connections": connection_manager.get_user_connections(target_user_id)
    }


@router.post("/notify/broadcast")
async def send_broadcast_notification(
    message: str,
    priority: str = "info",
    current_user: User = Depends(get_current_user)
):
    """Send broadcast notification to all users (admin only)"""
    if current_user.role != "admin":
        return {"error": "Admin access required"}
    
    await notification_service.notify_system_update(message, priority)
    
    return {
        "message": "Broadcast notification sent",
        "total_connections": connection_manager.get_total_connections()
    }


# Background task to start heartbeat
@router.on_event("startup")
async def start_websocket_heartbeat():
    """Start WebSocket heartbeat background task"""
    from app.services.websocket_service import websocket_heartbeat
    asyncio.create_task(websocket_heartbeat())