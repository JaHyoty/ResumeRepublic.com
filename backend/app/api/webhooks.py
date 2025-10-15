from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, verify_token
from app.models.user import User
from app.models.job_posting import JobPosting
import json
import asyncio
import structlog
from typing import Dict, Set, Any, Optional
import uuid

logger = structlog.get_logger()

router = APIRouter()

# Store active connections
active_connections: Dict[str, Set[asyncio.Queue]] = {}

@router.get("/events")
async def webhook_events(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Generic webhook endpoint for real-time updates using Server-Sent Events (SSE)
    Handles all types of webhook events, not just job postings
    """
    try:
        # Verify token (you might want to implement proper token validation)
        # For now, we'll use a simple approach - in production, use proper JWT validation
        user_id = await verify_webhook_token(token, db)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook token"
            )

        # Create a unique connection ID
        connection_id = str(uuid.uuid4())
        
        # Create a queue for this connection
        message_queue = asyncio.Queue()
        
        # Add to active connections
        if user_id not in active_connections:
            active_connections[user_id] = set()
        active_connections[user_id].add(message_queue)

        logger.info(
            "Webhook connection established",
            user_id=user_id,
            connection_id=connection_id
        )

        async def event_generator():
            try:
                # Send initial connection event
                yield f"data: {json.dumps({'type': 'connected', 'connection_id': connection_id, 'timestamp': asyncio.get_event_loop().time()})}\n\n"
                
                while True:
                    try:
                        # Wait for messages with timeout
                        message = await asyncio.wait_for(message_queue.get(), timeout=30.0)
                        
                        # Send the message as SSE
                        yield f"data: {json.dumps(message)}\n\n"
                        
                        # Mark task as done
                        message_queue.task_done()
                        
                    except asyncio.TimeoutError:
                        # Send heartbeat to keep connection alive
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': asyncio.get_event_loop().time()})}\n\n"
                        
            except asyncio.CancelledError:
                logger.info("Webhook connection cancelled", connection_id=connection_id)
                raise
            except Exception as e:
                logger.error("Webhook connection error", error=str(e), connection_id=connection_id)
                raise
            finally:
                # Clean up connection
                if user_id in active_connections:
                    active_connections[user_id].discard(message_queue)
                    if not active_connections[user_id]:
                        del active_connections[user_id]
                
                logger.info("Webhook connection closed", connection_id=connection_id)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to establish webhook connection", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to establish webhook connection"
        )

async def verify_webhook_token(token: str, db: Session) -> int | None:
    """
    Verify webhook token and return user ID
    In production, implement proper JWT validation
    """
    try:
        # For now, we'll use the same token validation as the main API
        # In production, you might want separate webhook tokens
        
        payload = verify_token(token)
        if payload and "sub" in payload:
            user_id = int(payload["sub"])
            
            # Verify user exists
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return user_id
                
        return None
        
    except Exception as e:
        logger.error("Failed to verify webhook token", error=str(e))
        return None

# Generic webhook functions

async def send_webhook_event(
    user_id: int,
    event_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    status: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
):
    """
    Send a generic webhook event to all active connections for a user
    """
    if user_id not in active_connections:
        return

    message = {
        "type": event_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "status": status,
        "data": data or {},
        "timestamp": asyncio.get_event_loop().time(),
        "user_id": user_id
    }

    # Send to all active connections for this user
    for queue in active_connections[user_id].copy():
        try:
            await queue.put(message)
        except Exception as e:
            logger.error("Failed to send webhook message", error=str(e))
            # Remove failed connection
            active_connections[user_id].discard(queue)

async def send_entity_update(
    user_id: int,
    entity_type: str,
    entity_id: str,
    status: str,
    data: Optional[Dict[str, Any]] = None
):
    """
    Send an entity update webhook (generic)
    """
    await send_webhook_event(
        user_id=user_id,
        event_type=f"{entity_type}_status_update",
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        data=data
    )

async def send_entity_completed(
    user_id: int,
    entity_type: str,
    entity_id: str,
    data: Optional[Dict[str, Any]] = None
):
    """
    Send an entity completion webhook (generic)
    """
    await send_webhook_event(
        user_id=user_id,
        event_type=f"{entity_type}_completed",
        entity_type=entity_type,
        entity_id=entity_id,
        status="complete",
        data=data
    )

async def send_entity_failed(
    user_id: int,
    entity_type: str,
    entity_id: str,
    error_message: str
):
    """
    Send an entity failure webhook (generic)
    """
    await send_webhook_event(
        user_id=user_id,
        event_type=f"{entity_type}_failed",
        entity_type=entity_type,
        entity_id=entity_id,
        status="failed",
        data={"error": error_message}
    )

async def send_user_notification(
    user_id: int,
    notification_type: str,
    message: str,
    data: Optional[Dict[str, Any]] = None
):
    """
    Send a user notification webhook
    """
    await send_webhook_event(
        user_id=user_id,
        event_type="user_notification",
        data={
            "notification_type": notification_type,
            "message": message,
            **(data or {})
        }
    )

async def send_system_alert(
    user_id: int,
    alert_type: str,
    message: str,
    severity: str = "info",
    data: Optional[Dict[str, Any]] = None
):
    """
    Send a system alert webhook
    """
    await send_webhook_event(
        user_id=user_id,
        event_type="system_alert",
        data={
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            **(data or {})
        }
    )

# Export functions for use in other modules
__all__ = [
    "send_webhook_event",
    "send_entity_update",
    "send_entity_completed",
    "send_entity_failed",
    "send_user_notification",
    "send_system_alert"
]
