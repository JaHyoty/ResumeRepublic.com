"""
Webhook API — DynamoDB polling version.
Replaces SSE with a polling endpoint for resume generation status.
"""

import json
import asyncio
import structlog
from typing import Dict, Set, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dynamodb import DynamoDBClient, get_db
from app.core.auth import get_current_user, verify_token
from app.core.dynamodb_models import UserItem, build_gen_status_item, SK_GENSTATUS

logger = structlog.get_logger()

router = APIRouter()


# ---------------------------------------------------------------------------
# Polling endpoint (replaces SSE)
# ---------------------------------------------------------------------------

@router.get("/events")
async def get_events():
    """Fallback endpoint for SSE to prevent 404s in serverless environment."""
    return {"message": "Serverless mode: use entity polling endpoints"}


@router.get("/status/{resume_id}")
async def get_generation_status(
    resume_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """
    Poll for resume generation status.
    Frontend should call this every 3 seconds until status is 'completed' or 'failed'.
    """
    item = db.get_item(f"USER#{current_user.id}", f"{SK_GENSTATUS}{resume_id}")
    if not item:
        return {
            "resume_id": resume_id,
            "status": "unknown",
            "message": "No status available yet",
        }

    return {
        "resume_id": resume_id,
        "status": item.get("status", "unknown"),
        "message": item.get("message"),
        "data": item.get("data"),
        "updated_at": item.get("updated_at"),
    }


# ---------------------------------------------------------------------------
# Status update functions (re-exported from app.services.webhook_service)
# ---------------------------------------------------------------------------

from app.services.webhook_service import (
    send_webhook_event,
    send_entity_update,
    send_entity_completed,
    send_entity_failed,
    send_user_notification,
    send_system_alert,
)

__all__ = [
    "send_webhook_event",
    "send_entity_update",
    "send_entity_completed",
    "send_entity_failed",
    "send_user_notification",
    "send_system_alert",
]
