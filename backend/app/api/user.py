"""
User management API routes — DynamoDB version
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.core.dynamodb import DynamoDBClient, get_db
from app.core.auth import get_current_user
from app.core.dynamodb_models import UserItem, SK_APP, SK_RESUME
from app.services.s3_service import s3_service
from app.schemas.user import UserResponse, UserUpdate, TermsAgreementRequest

router = APIRouter()
logger = structlog.get_logger()


@router.get("/", response_model=UserResponse)
def get_current_user_info(
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get current user's information"""
    return current_user.to_dict()


@router.put("/", response_model=UserResponse)
def update_current_user(
    user_data: UserUpdate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Update current user's information"""
    try:
        update_data = user_data.model_dump(exclude_unset=True)
        if not update_data:
            return current_user.to_dict()

        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        updated = db.update_item(
            f"USER#{current_user.id}",
            "PROFILE",
            update_data,
        )
        return {k: v for k, v in updated.items()
                if k not in ("PK", "SK", "GSI1PK", "GSI1SK", "entity_type")}

    except Exception as e:
        logger.error(f"Failed to update user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.post("/accept-terms", response_model=UserResponse)
async def accept_terms(
    agreement_data: TermsAgreementRequest,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Accept terms and privacy policy"""
    if not agreement_data.terms_accepted or not agreement_data.privacy_policy_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both terms and privacy policy must be accepted",
        )

    now = datetime.now(timezone.utc).isoformat()
    updated = db.update_item(
        f"USER#{current_user.id}",
        "PROFILE",
        {
            "terms_accepted_at": now,
            "privacy_policy_accepted_at": now,
            "updated_at": now,
        },
    )

    logger.info("User accepted terms and privacy policy", user_id=current_user.id)

    return {k: v for k, v in updated.items()
            if k not in ("PK", "SK", "GSI1PK", "GSI1SK", "entity_type")}


@router.delete("/")
async def delete_user(
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Delete the current user's account and all associated data"""
    logger.info("Starting account deletion", user_id=current_user.id, email=current_user.email)

    try:
        user_pk = f"USER#{current_user.id}"

        # Get all resume versions to clean up S3
        resume_items = db.query(user_pk, sk_prefix=SK_RESUME)
        for rv in resume_items:
            try:
                if rv.get("s3_key"):
                    await s3_service.delete_pdf(rv["s3_key"])
                if rv.get("latex_s3_key"):
                    await s3_service.delete_latex(rv["latex_s3_key"])
            except Exception as e:
                logger.error(f"Failed to delete S3 files for resume {rv.get('id')}: {e}")

        # Get ALL items for this user (experiences, skills, etc.) and delete them
        all_items = db.query(user_pk)
        keys_to_delete = [{"PK": item["PK"], "SK": item["SK"]} for item in all_items]

        if keys_to_delete:
            db.batch_delete(keys_to_delete)

        logger.info("Account deleted successfully", user_id=current_user.id)
        return {"message": "Account deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete account: {e}", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account. Please try again.",
        )
