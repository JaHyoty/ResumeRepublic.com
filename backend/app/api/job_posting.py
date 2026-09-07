"""
Job posting API endpoints — DynamoDB version
"""

from fastapi import APIRouter, Depends, HTTPException, status
from urllib.parse import urlparse, parse_qs, urlunparse
from datetime import datetime, timezone
import structlog

from app.core.dynamodb import DynamoDBClient, get_db
from app.core.auth import get_current_user
from app.core.dynamodb_models import (
    UserItem, build_job_posting_item, build_fetch_attempt_item,
    SK_JOBPOST,
)
from app.schemas.job_posting import (
    JobPostingFetchRequest, JobPostingFetchResponse,
    JobPostingCreateRequest, JobPostingResponse,
)
from app.core.lambda_dispatch import invoke_scraper_lambda

logger = structlog.get_logger()
router = APIRouter()


def clean_utm_parameters(url: str) -> str:
    """Remove UTM and tracking parameters from URL"""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    utm_params = [
        "utm_source", "utm_medium", "utm_campaign",
        "utm_term", "utm_content", "utm_id", "_atxsrc",
    ]
    for param in utm_params:
        query_params.pop(param, None)

    if query_params:
        clean_query = "&".join(f"{k}={v[0]}" for k, v in query_params.items())
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, clean_query, parsed.fragment))
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, "", parsed.fragment))


@router.post("/fetch", response_model=JobPostingFetchResponse, status_code=status.HTTP_202_ACCEPTED)
async def fetch_job_posting(
    request: JobPostingFetchRequest,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Initiate job posting parsing from URL"""
    try:
        clean_url = clean_utm_parameters(str(request.url))
        parsed_url = urlparse(clean_url)
        domain = parsed_url.netloc.lower()

        # Check for existing job posting by URL (GSI1 lookup)
        existing = db.query_gsi1(f"JOBURL#{clean_url}", SK_JOBPOST)
        # Filter out manual postings
        existing = [e for e in existing if e.get("status") != "manual"]

        if existing:
            job = existing[0]
            jp_id = job["id"]

            if job["status"] == "complete":
                return JobPostingFetchResponse(
                    job_posting_id=jp_id,
                    status=job["status"],
                    message="Job posting already parsed successfully",
                )
            elif job["status"] in ("pending", "fetching"):
                return JobPostingFetchResponse(
                    job_posting_id=jp_id,
                    status=job["status"],
                    message="Job posting parsing already in progress",
                )
            elif job["status"] == "failed":
                # Retry failed
                db.update_item(f"JOBPOST#{jp_id}", SK_JOBPOST, {
                    "status": "pending",
                    "created_by_user_id": current_user.id,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                })
                invoke_scraper_lambda(str(jp_id))
                return JobPostingFetchResponse(
                    job_posting_id=jp_id,
                    status="pending",
                    message="Job posting parsing initiated",
                )

        # Create new job posting
        jp_id = db.next_uuid()
        jp_item = build_job_posting_item(
            job_posting_id=jp_id,
            url=clean_url,
            domain=domain,
            created_by_user_id=current_user.id,
            status="pending",
        )
        db.put_item(jp_item)

        invoke_scraper_lambda(str(jp_id))

        logger.info("Job posting parsing initiated", job_posting_id=jp_id, url=clean_url, user_id=current_user.id)
        return JobPostingFetchResponse(
            job_posting_id=jp_id,
            status="pending",
            message="Job posting parsing initiated",
        )

    except Exception as e:
        logger.error("Failed to initiate job posting parsing", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate job posting parsing",
        )


@router.post("/create", response_model=JobPostingResponse, status_code=status.HTTP_201_CREATED)
async def create_job_posting(
    request: JobPostingCreateRequest,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Manually create a job posting"""
    try:
        clean_url = None
        if request.url:
            clean_url = clean_utm_parameters(str(request.url))

        jp_id = db.next_uuid()
        jp_item = build_job_posting_item(
            job_posting_id=jp_id,
            url=None,  # Don't set URL for manual postings
            domain=None,
            created_by_user_id=current_user.id,
            title=request.title,
            company=request.company,
            description=request.description,
            status="manual",
            provenance={
                "method": "manual",
                "extractor": "user_input",
                "confidence": 1.0,
                "original_url": clean_url,
            },
        )
        db.put_item(jp_item)

        logger.info("Job posting created manually", job_posting_id=jp_id, user_id=current_user.id)
        return jp_item

    except Exception as e:
        logger.error("Failed to create job posting manually", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job posting",
        )


@router.get("/{job_posting_id}", response_model=JobPostingResponse)
async def get_job_posting(
    job_posting_id: str,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get job posting by ID"""
    try:
        jp = db.get_item(f"JOBPOST#{job_posting_id}", SK_JOBPOST)
        if not jp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")
        return jp
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job posting", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job posting",
        )
