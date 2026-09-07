"""
Applications API endpoints — DynamoDB version
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List
from datetime import datetime, timezone
import structlog

from app.core.dynamodb import DynamoDBClient, get_db
from app.core.auth import get_current_user
from app.core.dynamodb_models import (
    UserItem, build_application_item, build_job_posting_item,
    SK_APP, SK_RESUME, SK_JOBPOST,
)
from app.schemas.application import ApplicationUpdate, ApplicationResponse, ApplicationStats
from app.services.s3_service import s3_service

logger = structlog.get_logger()
router = APIRouter()


def _enrich_application(app_item: dict, db: DynamoDBClient) -> dict:
    """Attach job posting data to an application dict."""
    jp_id = app_item.get("job_posting_id")
    if jp_id:
        jp = db.get_item(f"JOBPOST#{jp_id}", SK_JOBPOST)
        if jp:
            app_item["job_title"] = jp.get("title")
            app_item["company"] = jp.get("company")
            app_item["job_description"] = jp.get("description")
    return app_item


@router.get("/", response_model=List[ApplicationResponse])
async def get_applications(
    skip: int = 0,
    limit: int = 100,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get all applications for the current user"""
    apps = db.query(f"USER#{current_user.id}", sk_prefix=SK_APP)
    # Sort by created_at desc
    apps.sort(key=lambda a: a.get("created_at") or "", reverse=True)

    # Enrich with job posting data
    for app in apps:
        _enrich_application(app, db)

    return apps[skip: skip + limit]


@router.get("/stats", response_model=ApplicationStats)
async def get_application_stats(
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get application statistics"""
    apps = db.query(f"USER#{current_user.id}", sk_prefix=SK_APP)
    total_applications = len(apps)
    online_assessments = sum(1 for a in apps if a.get("online_assessment"))
    interviews = sum(1 for a in apps if a.get("interview"))
    rejected = sum(1 for a in apps if a.get("rejected"))

    online_assessment_rate = (online_assessments / total_applications * 100) if total_applications > 0 else 0.0
    interview_rate = (interviews / total_applications * 100) if total_applications > 0 else 0.0
    rejection_rate = (rejected / total_applications * 100) if total_applications > 0 else 0.0

    return ApplicationStats(
        total_applications=total_applications,
        online_assessments=online_assessments,
        interviews=interviews,
        rejected=rejected,
        online_assessment_rate=round(online_assessment_rate, 1),
        interview_rate=round(interview_rate, 1),
        rejection_rate=round(rejection_rate, 1),
    )


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get a specific application"""
    app = db.get_item(f"USER#{current_user.id}", f"{SK_APP}{application_id}")
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    _enrich_application(app, db)
    return app


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    application_update: ApplicationUpdate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Update an application"""
    pk = f"USER#{current_user.id}"
    existing = db.get_item(pk, f"{SK_APP}{application_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    update_data = application_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    updated = db.update_item(pk, f"{SK_APP}{application_id}", update_data)
    _enrich_application(updated, db)

    logger.info("Application updated", application_id=application_id, user_id=current_user.id)
    return updated


@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Delete an application and its associated resume files from S3"""
    pk = f"USER#{current_user.id}"
    existing = db.get_item(pk, f"{SK_APP}{application_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    # Get resume versions for this application
    resume_items = db.query(pk, sk_prefix=f"{SK_RESUME}{application_id}#")
    for rv in resume_items:
        try:
            if rv.get("s3_key"):
                await s3_service.delete_pdf(rv["s3_key"])
            if rv.get("latex_s3_key"):
                await s3_service.delete_latex(rv["latex_s3_key"])
        except Exception as e:
            logger.error(f"Failed to delete S3 files for resume {rv.get('id')}: {e}")

    # Delete resume versions
    if resume_items:
        db.batch_delete([{"PK": r["PK"], "SK": r["SK"]} for r in resume_items])

    # Delete the application
    db.delete_item(pk, f"{SK_APP}{application_id}")

    logger.info("Application deleted", application_id=application_id, user_id=current_user.id)
    return {"message": "Application deleted successfully"}


@router.post("/{job_posting_id}", response_model=ApplicationResponse)
async def create_application_from_job_posting(
    job_posting_id: str,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Create an application from a parsed job posting"""
    try:
        jp = db.get_item(f"JOBPOST#{job_posting_id}", SK_JOBPOST)
        if not jp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")

        if jp.get("status") not in ("complete", "manual"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job posting parsing not complete",
            )

        if not jp.get("title") or not jp.get("description"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job posting data incomplete",
            )

        # Check for existing application
        apps = db.query(f"USER#{current_user.id}", sk_prefix=SK_APP)
        for app in apps:
            if app.get("job_posting_id") == job_posting_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already created an application for this job posting",
                )

        # Create application
        app_id = db.next_id("application")
        app_item = build_application_item(
            user_id=current_user.id,
            app_id=app_id,
            applied_date=jp.get("created_at"),
            job_posting_id=job_posting_id,
            application_metadata={
                "source": "web-ui",
                "original_url": jp.get("url"),
                "parsing_method": (jp.get("provenance") or {}).get("method", "unknown"),
            },
        )
        db.put_item(app_item)

        logger.info(
            "Application created from job posting",
            application_id=app_id,
            job_posting_id=job_posting_id,
            user_id=current_user.id,
        )

        # Return with job posting data
        app_item["job_title"] = jp.get("title")
        app_item["company"] = jp.get("company")
        app_item["job_description"] = jp.get("description")
        return app_item

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create application from job posting", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application from job posting",
        )
