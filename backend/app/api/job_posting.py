"""
Job posting parsing API endpoints
Handles parsing of job postings from URLs
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import structlog
from urllib.parse import urlparse, urlunparse, parse_qs

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.job_posting import JobPosting, JobPostingFetchAttempt
from app.schemas.job_posting import (
    JobPostingFetchRequest,
    JobPostingFetchResponse,
    JobPostingResponse,
    JobPostingListResponse,
    JobPostingCreateRequest
)
from app.services.job_posting_parser import JobPostingParserService

logger = structlog.get_logger()

router = APIRouter()


def clean_utm_parameters(url: str) -> str:
    """
    Remove UTM parameters from URL while preserving other necessary parameters
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # Remove UTM parameters
    utm_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'utm_id']
    for param in utm_params:
        query_params.pop(param, None)
    
    # Rebuild query string
    if query_params:
        # Flatten the query parameters (parse_qs returns lists)
        clean_query = '&'.join([f"{k}={v[0]}" for k, v in query_params.items()])
        clean_url = urlunparse((
            parsed.scheme, parsed.netloc, parsed.path, 
            parsed.params, clean_query, parsed.fragment
        ))
    else:
        clean_url = urlunparse((
            parsed.scheme, parsed.netloc, parsed.path, 
            parsed.params, '', parsed.fragment
        ))
    
    return clean_url


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
        # Clean UTM parameters from URL
        clean_url = clean_utm_parameters(str(request.url))
        
        # Extract domain from cleaned URL
        parsed_url = urlparse(clean_url)
        domain = parsed_url.netloc.lower()
        
        # Check if job posting already exists (using cleaned URL)
        # Exclude manual postings to prevent users from seeing potentially false data
        existing_job = db.query(JobPosting).filter(
            JobPosting.url == clean_url,
            JobPosting.status != 'manual'
        ).first()
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
            url=clean_url,
            domain=domain,
            created_by_user_id=current_user.id,
            status='pending'
        )
        
        db.add(job_posting)
        db.commit()
        db.refresh(job_posting)
        
        # Add background task for parsing
        background_tasks.add_task(
            JobPostingParserService.process_job_posting_async,
            str(job_posting.id)
        )
        
        logger.info(
            "Job posting parsing initiated",
            job_posting_id=job_posting.id,
            url=clean_url,
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


@router.post("/create", response_model=JobPostingResponse, status_code=status.HTTP_201_CREATED)
async def create_job_posting(
    request: JobPostingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually create a job posting with provided data
    Used when user provides job data manually instead of parsing from URL
    """
    try:
        # Clean URL if provided
        clean_url = None
        domain = None
        if request.url:
            clean_url = clean_utm_parameters(str(request.url))
            parsed_url = urlparse(clean_url)
            domain = parsed_url.netloc.lower()
        
        # Create job posting record
        job_posting = JobPosting(
            url=clean_url,
            domain=domain,
            created_by_user_id=current_user.id,
            title=request.title,
            company=request.company,
            description=request.description,
            status='manual',
            provenance={
                "method": "manual",
                "extractor": "user_input",
                "confidence": 1.0,
                "timestamp": None  # Will be set by database
            }
        )
        
        db.add(job_posting)
        db.commit()
        db.refresh(job_posting)
        
        logger.info(
            "Job posting created manually",
            job_posting_id=job_posting.id,
            title=request.title,
            company=request.company,
            user_id=current_user.id
        )
        
        return JobPostingResponse.from_orm(job_posting)
        
    except Exception as e:
        logger.error(
            "Failed to create job posting manually",
            error=str(e),
            title=request.title,
            company=request.company,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job posting"
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



