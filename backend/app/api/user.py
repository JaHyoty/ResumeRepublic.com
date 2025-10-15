"""
User management API routes
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.application import Application
from app.models.resume import ResumeVersion
from app.services.s3_service import s3_service
from app.schemas.user import UserResponse, UserUpdate, TermsAgreementRequest

router = APIRouter()
logger = structlog.get_logger()


@router.get("/", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's information"""
    return current_user


@router.put("/", response_model=UserResponse)
def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's information"""
    try:
        # Update only provided fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        db.commit()
        db.refresh(current_user)
        return current_user
        
    except Exception as e:
        logger.error(f"Failed to update user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.post("/accept-terms", response_model=UserResponse)
async def accept_terms(
    agreement_data: TermsAgreementRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept terms and privacy policy"""
    
    if not agreement_data.terms_accepted or not agreement_data.privacy_policy_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both terms and privacy policy must be accepted"
        )
    
    # Update user agreement status
    current_user.terms_accepted_at = datetime.utcnow()
    current_user.privacy_policy_accepted_at = datetime.utcnow()
    
    db.commit()
    db.refresh(current_user)
    
    logger.info("User accepted terms and privacy policy", 
               user_id=current_user.id)
    
    return current_user


@router.delete("/")
async def delete_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete the current user's account and all associated data"""
    
    logger.info("Starting account deletion", user_id=current_user.id, email=current_user.email)
    
    try:
        # Get all applications for this user
        applications = db.query(Application).filter(
            Application.user_id == current_user.id
        ).all()
        
        # Delete S3 files for all applications
        if applications:
            
            for application in applications:
                # Get all resume versions for this application
                resume_versions = db.query(ResumeVersion).filter(
                    ResumeVersion.application_id == application.id
                ).all()
                
                # Delete S3 files for each resume version
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
        
        # Delete the user (this will cascade delete all related data due to foreign key constraints)
        db.delete(current_user)
        db.commit()
        
        logger.info("Account deleted successfully", user_id=current_user.id, email=current_user.email)
        return {"message": "Account deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete account: {e}", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account. Please try again."
        )
