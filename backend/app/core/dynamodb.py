"""
DynamoDB single-table client for serverless architecture.
Replaces SQLAlchemy/PostgreSQL with DynamoDB.

Single-table design:
  PK (partition key) + SK (sort key) encode entity type and ownership.
  GSI1 (GSI1PK + GSI1SK) supports email-based user lookups.

Entity key patterns:
  User:            PK=USER#<id>        SK=PROFILE
  Experience:      PK=USER#<uid>       SK=EXP#<id>
  ExperienceTitle: PK=USER#<uid>       SK=EXPTITLE#<eid>#<tid>
  Skill:           PK=USER#<uid>       SK=SKILL#<id>
  Education:       PK=USER#<uid>       SK=EDU#<id>
  Certification:   PK=USER#<uid>       SK=CERT#<id>
  Publication:     PK=USER#<uid>       SK=PUB#<id>
  Project:         PK=USER#<uid>       SK=PROJECT#<id>
  Website:         PK=USER#<uid>       SK=WEBSITE#<id>
  Application:     PK=USER#<uid>       SK=APP#<id>
  ResumeVersion:   PK=USER#<uid>       SK=RESUME#<appid>#<rid>
  JobPosting:      PK=JOBPOST#<id>     SK=JOBPOST
  FetchAttempt:    PK=JOBPOST#<jpid>   SK=ATTEMPT#<aid>
  GenStatus:       PK=USER#<uid>       SK=GENSTATUS#<rid>
  IDCounter:       PK=COUNTER          SK=<entity_type>
"""

import boto3
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from boto3.dynamodb.conditions import Key, Attr
import structlog

logger = structlog.get_logger()


def _serialize_value(value: Any) -> Any:
    """Convert Python types to DynamoDB-compatible types."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def _deserialize_value(value: Any) -> Any:
    """Convert DynamoDB types back to Python types."""
    if isinstance(value, Decimal):
        if value == int(value):
            return int(value)
        return float(value)
    if isinstance(value, dict):
        return {k: _deserialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deserialize_value(item) for item in value]
    return value


def _deserialize_item(item: Dict) -> Dict:
    """Deserialize an entire DynamoDB item."""
    return {k: _deserialize_value(v) for k, v in item.items()}


class DynamoDBClient:
    """
    DynamoDB single-table client.

    Provides CRUD operations with automatic key management
    and ID generation via atomic counters.
    """

    def __init__(self, table_name: str, region: str = "us-east-1"):
        self.table_name = table_name
        self.region = region
        self._dynamodb = boto3.resource("dynamodb", region_name=region)
        self._table = self._dynamodb.Table(table_name)
        logger.info("DynamoDB client initialized", table=table_name, region=region)

    # ------------------------------------------------------------------
    # ID Generation (atomic counter)
    # ------------------------------------------------------------------

    def next_id(self, entity_type: str) -> int:
        """
        Generate a monotonically increasing integer ID for the given entity type.
        Uses an atomic counter stored in the same DynamoDB table.
        """
        response = self._table.update_item(
            Key={"PK": "COUNTER", "SK": entity_type},
            UpdateExpression="SET current_value = if_not_exists(current_value, :start) + :inc",
            ExpressionAttributeValues={":start": Decimal("0"), ":inc": Decimal("1")},
            ReturnValues="UPDATED_NEW",
        )
        return int(response["Attributes"]["current_value"])

    def next_uuid(self) -> str:
        """Generate a new UUID string."""
        return str(uuid.uuid4())

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write an item to the table. Expects PK and SK to be set.
        Returns the serialised item that was written.
        """
        serialized = {k: _serialize_value(v) for k, v in item.items() if v is not None}
        self._table.put_item(Item=serialized)
        return serialized

    def get_item(self, pk: str, sk: str) -> Optional[Dict[str, Any]]:
        """Fetch a single item by its composite key."""
        response = self._table.get_item(Key={"PK": pk, "SK": sk})
        item = response.get("Item")
        return _deserialize_item(item) if item else None

    def update_item(
        self,
        pk: str,
        sk: str,
        updates: Dict[str, Any],
        condition_expression=None,
    ) -> Dict[str, Any]:
        """
        Partial update: only touches the supplied attributes.
        Returns the full updated item.
        """
        if not updates:
            return self.get_item(pk, sk) or {}

        expr_parts = []
        attr_names = {}
        attr_values = {}

        for i, (key, value) in enumerate(updates.items()):
            placeholder_name = f"#attr{i}"
            placeholder_value = f":val{i}"
            expr_parts.append(f"{placeholder_name} = {placeholder_value}")
            attr_names[placeholder_name] = key
            attr_values[placeholder_value] = _serialize_value(value)

        update_expr = "SET " + ", ".join(expr_parts)

        kwargs: Dict[str, Any] = {
            "Key": {"PK": pk, "SK": sk},
            "UpdateExpression": update_expr,
            "ExpressionAttributeNames": attr_names,
            "ExpressionAttributeValues": attr_values,
            "ReturnValues": "ALL_NEW",
        }
        if condition_expression:
            kwargs["ConditionExpression"] = condition_expression

        response = self._table.update_item(**kwargs)
        return _deserialize_item(response.get("Attributes", {}))

    def delete_item(self, pk: str, sk: str) -> None:
        """Delete a single item by its composite key."""
        self._table.delete_item(Key={"PK": pk, "SK": sk})

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def query(
        self,
        pk: str,
        sk_prefix: Optional[str] = None,
        sk_exact: Optional[str] = None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
        scan_forward: bool = True,
        filter_expression=None,
    ) -> List[Dict[str, Any]]:
        """
        Query items sharing the same partition key.

        sk_prefix: SK begins_with filter
        sk_exact: SK equals exact match
        index_name: use a GSI instead of the base table
        """
        pk_attr = "GSI1PK" if index_name == "GSI1" else "PK"
        sk_attr = "GSI1SK" if index_name == "GSI1" else "SK"

        key_condition = Key(pk_attr).eq(pk)
        if sk_exact:
            key_condition = key_condition & Key(sk_attr).eq(sk_exact)
        elif sk_prefix:
            key_condition = key_condition & Key(sk_attr).begins_with(sk_prefix)

        kwargs: Dict[str, Any] = {
            "KeyConditionExpression": key_condition,
            "ScanIndexForward": scan_forward,
        }
        if index_name:
            kwargs["IndexName"] = index_name
        if limit:
            kwargs["Limit"] = limit
        if filter_expression:
            kwargs["FilterExpression"] = filter_expression

        items = []
        while True:
            response = self._table.query(**kwargs)
            items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            kwargs["ExclusiveStartKey"] = last_key

        return [_deserialize_item(item) for item in items]

    def query_gsi1(
        self,
        gsi1pk: str,
        gsi1sk: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Convenience wrapper to query GSI1."""
        return self.query(
            pk=gsi1pk,
            sk_exact=gsi1sk,
            index_name="GSI1",
        )

    def batch_write(self, items: List[Dict[str, Any]]) -> None:
        """Write multiple items in batches of 25."""
        with self._table.batch_writer() as batch:
            for item in items:
                serialized = {k: _serialize_value(v) for k, v in item.items() if v is not None}
                batch.put_item(Item=serialized)

    def batch_delete(self, keys: List[Dict[str, str]]) -> None:
        """Delete multiple items by their keys."""
        with self._table.batch_writer() as batch:
            for key in keys:
                batch.delete_item(Key=key)

    def scan(self, filter_expression=None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Full table scan. Use sparingly!
        Primarily for admin/migration scripts.
        """
        kwargs: Dict[str, Any] = {}
        if filter_expression:
            kwargs["FilterExpression"] = filter_expression
        if limit:
            kwargs["Limit"] = limit

        items = []
        while True:
            response = self._table.scan(**kwargs)
            items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            kwargs["ExclusiveStartKey"] = last_key

        return [_deserialize_item(item) for item in items]


# ---------------------------------------------------------------------------
# Global instance: initialised lazily from settings
# ---------------------------------------------------------------------------

_db_client: Optional[DynamoDBClient] = None


def get_dynamodb_client() -> DynamoDBClient:
    """Get or create the global DynamoDB client singleton."""
    global _db_client
    if _db_client is None:
        from app.core.settings import settings
        _db_client = DynamoDBClient(
            table_name=settings.DYNAMODB_TABLE_NAME,
            region=settings.AWS_REGION,
        )
    return _db_client


def get_db() -> DynamoDBClient:
    """
    FastAPI dependency: drop-in replacement for the old get_db().
    No session lifecycle to manage with DynamoDB.
    """
    return get_dynamodb_client()
