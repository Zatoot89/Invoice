"""
InvoiceFlow Pro - WebSocket Real-time Notification Service
"""
import json
import asyncio
from typing import Dict, Set, Any, Optional, List
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import structlog

from app.core.security import get_token_subject
from app.core.exceptions import AuthenticationException

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """
    WebSocket connection manager for real-time notifications
    """
    
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int, metadata: Optional[Dict[str, Any]] = None):
        """Accept a WebSocket connection and associate it with a user"""
        await websocket.accept()
        
        # Add to user's connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Store connection info
        self.connection_info[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        logger.info(f"WebSocket connected for user {user_id}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "message": "Connected to InvoiceFlow Pro",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.connection_info:
            user_id = self.connection_info[websocket]["user_id"]
            
            # Remove from user's connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove connection info
            del self.connection_info[websocket]
            
            logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket: {str(e)}")
            self.disconnect(websocket)
    
    async def send_user_message(self, message: Dict[str, Any], user_id: int):
        """Send a message to all connections of a specific user"""
        if user_id in self.active_connections:
            # Send to all user's connections
            connections = self.active_connections[user_id].copy()
            for websocket in connections:
                await self.send_personal_message(message, websocket)
    
    async def send_broadcast_message(self, message: Dict[str, Any]):
        """Send a message to all connected users"""
        for user_id in self.active_connections:
            await self.send_user_message(message, user_id)
    
    def get_user_connections(self, user_id: int) -> int:
        """Get number of active connections for a user"""
        return len(self.active_connections.get(user_id, set()))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_connected_users(self) -> List[int]:
        """Get list of connected user IDs"""
        return list(self.active_connections.keys())


class NotificationService:
    """
    Service for managing real-time notifications
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def notify_invoice_created(self, user_id: int, invoice_data: Dict[str, Any]):
        """Notify user when an invoice is created"""
        message = {
            "type": "invoice_created",
            "title": "New Invoice Created",
            "message": f"Invoice {invoice_data['invoice_number']} has been created",
            "data": {
                "invoice_id": invoice_data["id"],
                "invoice_number": invoice_data["invoice_number"],
                "customer_name": invoice_data["customer_name"],
                "total": invoice_data["total"],
                "currency": invoice_data["currency"]
            },
            "timestamp": datetime.utcnow().isoformat(),
            "action_url": f"/invoices/{invoice_data['id']}"
        }
        
        await self.connection_manager.send_user_message(message, user_id)
    
    async def notify_invoice_sent(self, user_id: int, invoice_data: Dict[str, Any]):
        """Notify user when an invoice is sent"""
        message = {
            "type": "invoice_sent",
            "title": "Invoice Sent",
            "message": f"Invoice {invoice_data['invoice_number']} has been sent to {invoice_data['customer_name']}",
            "data": {
                "invoice_id": invoice_data["id"],
                "invoice_number": invoice_data["invoice_number"],
                "customer_name": invoice_data["customer_name"],
                "sent_at": invoice_data.get("sent_date")
            },
            "timestamp": datetime.utcnow().isoformat(),
            "action_url": f"/invoices/{invoice_data['id']}"
        }
        
        await self.connection_manager.send_user_message(message, user_id)
    
    async def notify_payment_received(self, user_id: int, payment_data: Dict[str, Any]):
        """Notify user when a payment is received"""
        message = {
            "type": "payment_received",
            "title": "Payment Received",
            "message": f"Payment of {payment_data['currency']} {payment_data['amount']} received for Invoice {payment_data['invoice_number']}",
            "data": {
                "payment_id": payment_data["id"],
                "invoice_id": payment_data["invoice_id"],
                "invoice_number": payment_data["invoice_number"],
                "amount": payment_data["amount"],
                "currency": payment_data["currency"],
                "payment_method": payment_data["payment_method"]
            },
            "timestamp": datetime.utcnow().isoformat(),
            "action_url": f"/invoices/{payment_data['invoice_id']}"
        }
        
        await self.connection_manager.send_user_message(message, user_id)
    
    async def notify_invoice_overdue(self, user_id: int, invoice_data: Dict[str, Any]):
        """Notify user when an invoice becomes overdue"""
        message = {
            "type": "invoice_overdue",
            "title": "Invoice Overdue",
            "message": f"Invoice {invoice_data['invoice_number']} is now overdue",
            "data": {
                "invoice_id": invoice_data["id"],
                "invoice_number": invoice_data["invoice_number"],
                "customer_name": invoice_data["customer_name"],
                "amount_due": invoice_data["amount_due"],
                "currency": invoice_data["currency"],
                "days_overdue": invoice_data.get("days_overdue", 0)
            },
            "timestamp": datetime.utcnow().isoformat(),
            "action_url": f"/invoices/{invoice_data['id']}",
            "priority": "high"
        }
        
        await self.connection_manager.send_user_message(message, user_id)
    
    async def notify_customer_created(self, user_id: int, customer_data: Dict[str, Any]):
        """Notify user when a customer is created"""
        message = {
            "type": "customer_created",
            "title": "New Customer Added",
            "message": f"Customer {customer_data['name']} has been added",
            "data": {
                "customer_id": customer_data["id"],
                "customer_name": customer_data["name"],
                "email": customer_data["email"],
                "company": customer_data.get("company")
            },
            "timestamp": datetime.utcnow().isoformat(),
            "action_url": f"/customers/{customer_data['id']}"
        }
        
        await self.connection_manager.send_user_message(message, user_id)
    
    async def notify_system_update(self, message_text: str, priority: str = "info"):
        """Send system-wide notification"""
        message = {
            "type": "system_update",
            "title": "System Update",
            "message": message_text,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": priority
        }
        
        await self.connection_manager.send_broadcast_message(message)
    
    async def notify_user_activity(self, user_id: int, activity_data: Dict[str, Any]):
        """Notify user about their activity"""
        message = {
            "type": "user_activity",
            "title": activity_data.get("title", "Activity Update"),
            "message": activity_data.get("message", "New activity on your account"),
            "data": activity_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.send_user_message(message, user_id)
    
    async def send_typing_indicator(self, user_id: int, is_typing: bool):
        """Send typing indicator for live chat/comments"""
        message = {
            "type": "typing_indicator",
            "user_id": user_id,
            "is_typing": is_typing,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # This would typically be sent to other users in the same context
        await self.connection_manager.send_broadcast_message(message)
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            "total_connections": self.connection_manager.get_total_connections(),
            "connected_users": len(self.connection_manager.get_connected_users()),
            "user_connections": {
                user_id: len(connections)
                for user_id, connections in self.connection_manager.active_connections.items()
            }
        }


# Global instances
connection_manager = ConnectionManager()
notification_service = NotificationService(connection_manager)


async def authenticate_websocket(websocket: WebSocket, token: str) -> int:
    """
    Authenticate WebSocket connection using JWT token
    """
    try:
        user_id = get_token_subject(token)
        return int(user_id)
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {str(e)}")
        await websocket.close(code=1008, reason="Authentication failed")
        raise AuthenticationException("Invalid token")


async def handle_websocket_message(websocket: WebSocket, message_data: Dict[str, Any]):
    """
    Handle incoming WebSocket messages from client
    """
    message_type = message_data.get("type")
    
    if message_type == "ping":
        # Respond to ping with pong
        await connection_manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
    
    elif message_type == "typing":
        # Handle typing indicator
        user_id = connection_manager.connection_info[websocket]["user_id"]
        is_typing = message_data.get("is_typing", False)
        await notification_service.send_typing_indicator(user_id, is_typing)
    
    elif message_type == "subscribe":
        # Handle subscription to specific events
        # This could be extended to subscribe to specific invoice/customer updates
        pass
    
    else:
        logger.warning(f"Unhandled WebSocket message type: {message_type}")


async def websocket_heartbeat():
    """
    Background task to send periodic heartbeat messages
    """
    while True:
        if connection_manager.get_total_connections() > 0:
            heartbeat_message = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
                "connections": connection_manager.get_total_connections()
            }
            await connection_manager.send_broadcast_message(heartbeat_message)
        
        # Wait 30 seconds before next heartbeat
        await asyncio.sleep(30)