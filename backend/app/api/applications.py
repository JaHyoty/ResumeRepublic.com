"""
Applications API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List
import structlog

from app.core.database import get_db
from app.models.application import Application
from app.models.job_posting import JobPosting
from app.models.resume import ResumeVersion
from app.schemas.application import (
    ApplicationUpdate, 
    ApplicationResponse, 
    ApplicationStats
)
from app.core.auth import get_current_user
from app.models.user import User
from app.services.s3_service import s3_service

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=List[ApplicationResponse])
async def get_applications(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all applications for the current user, ordered by ID (newest first)"""
    applications = db.query(Application).options(
        joinedload(Application.job_posting)
    ).filter(
        Application.user_id == current_user.id
    ).order_by(Application.id.desc()).offset(skip).limit(limit).all()
    
    # Convert to response format with job posting data
    response_data = []
    for app in applications:
        app_data = {
            "id": app.id,
            "applied_date": app.applied_date,
            "created_at": app.created_at,
            "updated_at": app.updated_at,
            "online_assessment": app.online_assessment,
            "interview": app.interview,
            "rejected": app.rejected,
            "salary_range": app.salary_range,
            "location": app.location,
            "job_type": app.job_type,
            "experience_level": app.experience_level,
            "application_metadata": app.application_metadata,
            "job_posting_id": app.job_posting_id,
            "job_title": app.job_posting.title if app.job_posting else None,
            "company": app.job_posting.company if app.job_posting else None,
            "job_description": app.job_posting.description if app.job_posting else None
        }
        response_data.append(app_data)
    
    return response_data


@router.get("/stats", response_model=ApplicationStats)
async def get_application_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get application statistics for the current user"""
    # Get total count
    total_applications = db.query(Application).filter(
        Application.user_id == current_user.id
    ).count()
    
    # Get counts for each status
    online_assessments = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.online_assessment == True
    ).count()
    
    interviews = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.interview == True
    ).count()
    
    rejected = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.rejected == True
    ).count()
    
    # Calculate rates
    online_assessment_rate = (online_assessments / total_applications * 100) if total_applications > 0 else 0
    interview_rate = (interviews / total_applications * 100) if total_applications > 0 else 0
    rejection_rate = (rejected / total_applications * 100) if total_applications > 0 else 0
    
    return ApplicationStats(
        total_applications=total_applications,
        online_assessments=online_assessments,
        interviews=interviews,
        rejected=rejected,
        online_assessment_rate=round(online_assessment_rate, 1),
        interview_rate=round(interview_rate, 1),
        rejection_rate=round(rejection_rate, 1)
    )


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific application by ID"""
    application = db.query(Application).options(
        joinedload(Application.job_posting)
    ).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Return application with job posting data
    return ApplicationResponse(
        id=application.id,
        applied_date=application.applied_date,
        created_at=application.created_at,
        updated_at=application.updated_at,
        job_title=application.job_posting.title if application.job_posting else None,
        company=application.job_posting.company if application.job_posting else None,
        job_description=application.job_posting.description if application.job_posting else None
    )


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    application_update: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an application"""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Update only provided fields
    update_data = application_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(application, field, value)
    
    db.commit()
    db.refresh(application)
    
    # Reload with job posting data
    application_with_job = db.query(Application).options(
        joinedload(Application.job_posting)
    ).filter(Application.id == application_id).first()
    
    logger.info("Application updated", application_id=application_id, user_id=current_user.id)
    
    # Return properly formatted response with job posting data
    return ApplicationResponse(
        id=application_with_job.id,
        applied_date=application_with_job.applied_date,
        created_at=application_with_job.created_at,
        updated_at=application_with_job.updated_at,
        online_assessment=application_with_job.online_assessment,
        interview=application_with_job.interview,
        rejected=application_with_job.rejected,
        salary_range=application_with_job.salary_range,
        location=application_with_job.location,
        job_type=application_with_job.job_type,
        experience_level=application_with_job.experience_level,
        application_metadata=application_with_job.application_metadata,
        job_posting_id=application_with_job.job_posting_id,
        job_title=application_with_job.job_posting.title if application_with_job.job_posting else None,
        company=application_with_job.job_posting.company if application_with_job.job_posting else None,
        job_description=application_with_job.job_posting.description if application_with_job.job_posting else None
    )


@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an application and its associated resume files from S3"""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Get all resume versions for this application before deleting
    resume_versions = db.query(ResumeVersion).filter(
        ResumeVersion.application_id == application_id
    ).all()
    
    # Delete S3 files for each resume version
    if resume_versions:
        
        for resume_version in resume_versions:
            try:
                # Delete PDF from S3 if it exists
                if resume_version.s3_key:
                    await s3_service.delete_pdf(resume_version.s3_key)
                    logger.info(f"Deleted PDF from S3: {resume_version.s3_key}")
                
                # Delete LaTeX file from S3 if it exists
                if resume_version.latex_s3_key:
                    await s3_service.delete_latex(resume_version.latex_s3_key)
                    logger.info(f"Deleted LaTeX file from S3: {resume_version.latex_s3_key}")
                    
            except Exception as e:
                logger.error(f"Failed to delete S3 files for resume version {resume_version.id}: {e}")
                # Continue with deletion even if S3 cleanup fails
    
    # Delete the application (resume versions will be deleted by cascade)
    db.delete(application)
    db.commit()
    
    logger.info("Application deleted", application_id=application_id, user_id=current_user.id)
    return {"message": "Application deleted successfully"}


# Job Posting Integration

@router.post("/{job_posting_id}", response_model=ApplicationResponse)
async def create_application_from_job_posting(
    job_posting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create an application from a parsed job posting
    """
    try:
        job_posting = db.query(JobPosting).filter(JobPosting.id == job_posting_id).first()
        
        if not job_posting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )
        
        if job_posting.status not in ['complete', 'manual']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job posting parsing not complete"
            )
        
        if not job_posting.title or not job_posting.description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job posting data incomplete"
            )
        
        # Check if user already has an application for this job posting
        existing_application = db.query(Application).filter(
            Application.user_id == current_user.id,
            Application.job_posting_id == job_posting_id
        ).first()
        
        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already created an application for this job posting"
            )
        
        # Create application linked to job posting
        application = Application(
            user_id=current_user.id,
            applied_date=job_posting.created_at,
            job_posting_id=job_posting.id,
            application_metadata={
                "source": "web-ui",
                "original_url": job_posting.url,
                "parsing_method": job_posting.provenance.get('method', 'unknown') if job_posting.provenance else 'unknown'
            }
        )
        
        db.add(application)
        db.commit()
        db.refresh(application)
        
        logger.info(
            "Application created from job posting",
            application_id=application.id,
            job_posting_id=job_posting.id,
            user_id=current_user.id
        )
        
        # Return application with job posting data
        return ApplicationResponse(
            id=application.id,
            applied_date=application.applied_date,
            created_at=application.created_at,
            updated_at=application.updated_at,
            job_title=job_posting.title,
            company=job_posting.company,
            job_description=job_posting.description
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create application from job posting",
            error=str(e),
            job_posting_id=job_posting_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application from job posting"
        )
