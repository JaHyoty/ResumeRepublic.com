"""
Database configuration — DynamoDB serverless version.
Provides get_db() dependency and background task helper
that return the DynamoDB client.
"""

from typing import Optional
from contextlib import contextmanager
import structlog

from app.core.dynamodb import DynamoDBClient, get_dynamodb_client

logger = structlog.get_logger()

# Re-export for backward compatibility
get_db = lambda: get_dynamodb_client()


@contextmanager
def get_db_for_background_task():
    """
    Context manager for background tasks to get DynamoDB client.
    With DynamoDB there is no session to manage, so this just yields the client.
    """
    db = get_dynamodb_client()
    try:
        yield db
    except Exception as e:
        logger.error("Error in background task", error=str(e))
        raise
