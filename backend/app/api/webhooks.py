from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.job_posting import JobPosting
import json
import asyncio
import structlog
from typing import Dict, Set
import uuid

logger = structlog.get_logger()

router = APIRouter()

# Store active connections
active_connections: Dict[str, Set[asyncio.Queue]] = {}

@router.get("/job-postings")
async def job_posting_webhook(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for job posting status updates using Server-Sent Events (SSE)
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
                yield f"data: {json.dumps({'type': 'connected', 'connection_id': connection_id})}\n\n"
                
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
        from app.core.auth import verify_token
        
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

async def send_job_posting_update(
    user_id: int,
    job_posting_id: str,
    status: str,
    data: dict = None
):
    """
    Send job posting update to all active connections for a user
    """
    if user_id not in active_connections:
        return

    message = {
        "type": "job_posting_status_update",
        "job_posting_id": job_posting_id,
        "status": status,
        "data": data or {},
        "timestamp": asyncio.get_event_loop().time()
    }

    # Send to all active connections for this user
    for queue in active_connections[user_id].copy():
        try:
            await queue.put(message)
        except Exception as e:
            logger.error("Failed to send webhook message", error=str(e))
            # Remove failed connection
            active_connections[user_id].discard(queue)

async def send_job_posting_completed(
    user_id: int,
    job_posting_id: str,
    job_posting_data: dict
):
    """
    Send job posting completion notification
    """
    if user_id not in active_connections:
        return

    message = {
        "type": "job_posting_completed",
        "job_posting_id": job_posting_id,
        "status": "complete",
        "data": job_posting_data,
        "timestamp": asyncio.get_event_loop().time()
    }

    for queue in active_connections[user_id].copy():
        try:
            await queue.put(message)
        except Exception as e:
            logger.error("Failed to send completion webhook", error=str(e))
            active_connections[user_id].discard(queue)

async def send_job_posting_failed(
    user_id: int,
    job_posting_id: str,
    error_message: str
):
    """
    Send job posting failure notification
    """
    if user_id not in active_connections:
        return

    message = {
        "type": "job_posting_failed",
        "job_posting_id": job_posting_id,
        "status": "failed",
        "data": {"error": error_message},
        "timestamp": asyncio.get_event_loop().time()
    }

    for queue in active_connections[user_id].copy():
        try:
            await queue.put(message)
        except Exception as e:
            logger.error("Failed to send failure webhook", error=str(e))
            active_connections[user_id].discard(queue)

# Export functions for use in other modules
__all__ = [
    "send_job_posting_update",
    "send_job_posting_completed", 
    "send_job_posting_failed"
]
