"""
Applications API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import structlog

from app.core.database import get_db
from app.models.application import Application
from app.schemas.application import (
    ApplicationCreate, 
    ApplicationUpdate, 
    ApplicationResponse, 
    ApplicationStats
)
from app.core.auth import get_current_user
from app.models.user import User

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
    applications = db.query(Application).filter(
        Application.user_id == current_user.id
    ).order_by(Application.id.desc()).offset(skip).limit(limit).all()
    
    return applications


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


@router.post("/", response_model=ApplicationResponse)
async def create_application(
    application: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new application"""
    db_application = Application(
        user_id=current_user.id,
        **application.dict()
    )
    
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    
    logger.info("Application created", application_id=db_application.id, user_id=current_user.id)
    return db_application


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific application by ID"""
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    return application


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
    
    logger.info("Application updated", application_id=application_id, user_id=current_user.id)
    return application


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
    from app.models.resume import ResumeVersion
    resume_versions = db.query(ResumeVersion).filter(
        ResumeVersion.application_id == application_id
    ).all()
    
    # Delete S3 files for each resume version
    if resume_versions:
        from app.services.s3_service import s3_service
        
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
