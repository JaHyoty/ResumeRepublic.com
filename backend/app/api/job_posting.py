"""
Job posting parsing API endpoints
Handles parsing of job postings from URLs
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import structlog
from urllib.parse import urlparse

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.job_posting import JobPosting, DomainSelector, JobPostingFetchAttempt
from app.schemas.job_posting import (
    JobPostingFetchRequest,
    JobPostingFetchResponse,
    JobPostingUpdateRequest,
    JobPostingResponse,
    JobPostingListResponse,
    DomainSelectorResponse,
    FetchAttemptResponse
)
from app.services.job_posting_parser import JobPostingParserService

logger = structlog.get_logger()

router = APIRouter()


@router.post("/fetch", response_model=JobPostingFetchResponse, status_code=status.HTTP_202_ACCEPTED)
async def fetch_job_posting(
    request: JobPostingFetchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate job posting parsing from URL
    Returns immediately with job ID, processing happens in background
    """
    try:
        # Extract domain from URL
        parsed_url = urlparse(str(request.url))
        domain = parsed_url.netloc.lower()
        
        # Check if job posting already exists
        existing_job = db.query(JobPosting).filter(JobPosting.url == str(request.url)).first()
        if existing_job:
            if existing_job.status == 'complete':
                return JobPostingFetchResponse(
                    job_posting_id=existing_job.id,
                    status=existing_job.status,
                    message="Job posting already parsed successfully"
                )
            elif existing_job.status in ['pending', 'fetching']:
                return JobPostingFetchResponse(
                    job_posting_id=existing_job.id,
                    status=existing_job.status,
                    message="Job posting parsing already in progress"
                )
        
        # Create new job posting record
        job_posting = JobPosting(
            url=str(request.url),
            domain=domain,
            status='pending'
        )
        
        db.add(job_posting)
        db.commit()
        db.refresh(job_posting)
        
        # Enqueue background task for parsing
        background_tasks.add_task(
            JobPostingParserService.process_job_posting,
            job_posting.id,
            db
        )
        
        logger.info(
            "Job posting parsing initiated",
            job_posting_id=job_posting.id,
            url=str(request.url),
            domain=domain,
            user_id=current_user.id,
            source=request.source
        )
        
        return JobPostingFetchResponse(
            job_posting_id=job_posting.id,
            status='pending',
            message="Job posting parsing initiated"
        )
        
    except Exception as e:
        logger.error(
            "Failed to initiate job posting parsing",
            error=str(e),
            url=str(request.url),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate job posting parsing"
        )


@router.get("/{job_posting_id}", response_model=JobPostingResponse)
async def get_job_posting(
    job_posting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get job posting parsing status and extracted data
    """
    try:
        job_posting = db.query(JobPosting).filter(JobPosting.id == job_posting_id).first()
        
        if not job_posting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )
        
        return JobPostingResponse.from_orm(job_posting)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get job posting",
            error=str(e),
            job_posting_id=job_posting_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job posting"
        )


@router.put("/{job_posting_id}", response_model=JobPostingResponse)
async def update_job_posting(
    job_posting_id: str,
    request: JobPostingUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually update job posting data (override parsing results)
    Sets status to 'manual' to indicate manual override
    """
    try:
        job_posting = db.query(JobPosting).filter(JobPosting.id == job_posting_id).first()
        
        if not job_posting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )
        
        # Update fields if provided
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job_posting, field, value)
        
        # Set status to manual and update provenance
        job_posting.status = 'manual'
        job_posting.provenance = {
            "method": "manual",
            "extractor": "user_override",
            "confidence": 1.0,
            "timestamp": job_posting.updated_at.isoformat() if job_posting.updated_at else None
        }
        
        db.commit()
        db.refresh(job_posting)
        
        logger.info(
            "Job posting manually updated",
            job_posting_id=job_posting.id,
            user_id=current_user.id,
            updated_fields=list(update_data.keys())
        )
        
        return JobPostingResponse.from_orm(job_posting)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update job posting",
            error=str(e),
            job_posting_id=job_posting_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job posting"
        )


@router.get("/", response_model=JobPostingListResponse)
async def list_job_postings(
    page: int = 1,
    per_page: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List job postings with pagination and filtering
    """
    try:
        query = db.query(JobPosting)
        
        # Apply status filter if provided
        if status_filter:
            query = query.filter(JobPosting.status == status_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        job_postings = query.order_by(desc(JobPosting.created_at)).offset(offset).limit(per_page).all()
        
        return JobPostingListResponse(
            job_postings=[JobPostingResponse.from_orm(jp) for jp in job_postings],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(
            "Failed to list job postings",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job postings"
        )


@router.get("/{job_posting_id}/attempts", response_model=List[FetchAttemptResponse])
async def get_job_posting_attempts(
    job_posting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get fetch attempts for a specific job posting
    """
    try:
        # Verify job posting exists
        job_posting = db.query(JobPosting).filter(JobPosting.id == job_posting_id).first()
        if not job_posting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )
        
        attempts = db.query(JobPostingFetchAttempt).filter(
            JobPostingFetchAttempt.job_posting_id == job_posting_id
        ).order_by(desc(JobPostingFetchAttempt.created_at)).all()
        
        return [FetchAttemptResponse.from_orm(attempt) for attempt in attempts]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get job posting attempts",
            error=str(e),
            job_posting_id=job_posting_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job posting attempts"
        )


@router.get("/domains/selectors", response_model=List[DomainSelectorResponse])
async def list_domain_selectors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List domain selectors for debugging and management
    """
    try:
        selectors = db.query(DomainSelector).order_by(desc(DomainSelector.success_count)).all()
        return [DomainSelectorResponse.from_orm(selector) for selector in selectors]
        
    except Exception as e:
        logger.error(
            "Failed to list domain selectors",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve domain selectors"
        )
