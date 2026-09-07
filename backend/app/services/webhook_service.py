"""
Webhook status update service — DynamoDB polling version.
Decoupled from FastAPI so worker Lambdas (Scraper, PDF) can use it without web framework dependencies.
"""

from typing import Dict, Any, Optional
import structlog
from app.core.dynamodb_models import build_gen_status_item

logger = structlog.get_logger()


async def send_webhook_event(
    user_id: int,
    event_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    status: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
):
    """Write an entity status update to DynamoDB for polling."""
    from app.core.dynamodb import get_dynamodb_client
    db = get_dynamodb_client()

    if entity_id and entity_type:
        try:
            resume_id = int(entity_id)
        except (ValueError, TypeError):
            resume_id = hash(entity_id) % 1000000

        status_item = build_gen_status_item(
            user_id=user_id,
            resume_id=resume_id,
            status=status or event_type,
            message=f"{event_type}: {entity_type}",
            data=data,
        )
        db.put_item(status_item)


async def send_entity_update(
    user_id: int,
    entity_type: str,
    entity_id: str,
    status: str,
    data: Optional[Dict[str, Any]] = None,
):
    """Send an entity update (writes to DynamoDB status table)."""
    await send_webhook_event(
        user_id=user_id,
        event_type=f"{entity_type}_status_update",
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        data=data,
    )


async def send_entity_completed(
    user_id: int,
    entity_type: str,
    entity_id: str,
    data: Optional[Dict[str, Any]] = None,
):
    """Send an entity completion status."""
    await send_webhook_event(
        user_id=user_id,
        event_type=f"{entity_type}_completed",
        entity_type=entity_type,
        entity_id=entity_id,
        status="complete",
        data=data,
    )


async def send_entity_failed(
    user_id: int,
    entity_type: str,
    entity_id: str,
    error_message: str,
):
    """Send an entity failure status."""
    await send_webhook_event(
        user_id=user_id,
        event_type=f"{entity_type}_failed",
        entity_type=entity_type,
        entity_id=entity_id,
        status="failed",
        data={"error": error_message},
    )


async def send_user_notification(
    user_id: int,
    notification_type: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
):
    """Send a user notification (stores in DynamoDB for polling)."""
    await send_webhook_event(
        user_id=user_id,
        event_type="user_notification",
        data={
            "notification_type": notification_type,
            "message": message,
            **(data or {}),
        },
    )


async def send_system_alert(
    user_id: int,
    alert_type: str,
    message: str,
    severity: str = "info",
    data: Optional[Dict[str, Any]] = None,
):
    """Send a system alert."""
    await send_webhook_event(
        user_id=user_id,
        event_type="system_alert",
        data={
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            **(data or {}),
        },
    )


__all__ = [
    "send_webhook_event",
    "send_entity_update",
    "send_entity_completed",
    "send_entity_failed",
    "send_user_notification",
    "send_system_alert",
]
