"""
Resume generation API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import base64
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.application import Application
from app.models.resume import ResumeVersion
from app.services.latex_service import latex_service, LaTeXCompilationError

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/design")
def design_resume(
    resume_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Design an AI-optimized PDF resume from user data and job description
    Creates an application if one doesn't exist and stores resume version
    """
    try:
        # Get or create application
        application_id = resume_data.get('linked_application_id')
        if not application_id:
            # Create new application from job description
            job_description = resume_data.get('job_description', '')
            application = Application(
                user_id=current_user.id,
                job_title=resume_data.get('job_title', 'New Position'),
                company=resume_data.get('company', 'Target Company'),
                job_description=job_description,
                applied_date=datetime.now()
            )
            db.add(application)
            db.commit()
            db.refresh(application)
            application_id = application.id
        else:
            # Verify application belongs to user
            application = db.query(Application).filter(
                Application.id == application_id,
                Application.user_id == current_user.id
            ).first()
            if not application:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Application not found"
                )

        # Generate optimized PDF using LLM and LaTeX service
        pdf_content = latex_service.generate_optimized_resume_pdf(resume_data)
        
        # Encode PDF content as base64 for storage
        pdf_content_b64 = base64.b64encode(pdf_content).decode('utf-8')
        
        # Create resume version record
        resume_version = ResumeVersion(
            user_id=current_user.id,
            application_id=application_id,
            title=f"{resume_data.get('personal_info', {}).get('name', 'Resume')} - {application.company}",
            template_used=resume_data.get('template', 'professional'),
            pdf_content=pdf_content_b64,
            pdf_url=None,  # Will be set after commit when we have the ID
            resume_metadata={
                'job_description': resume_data.get('job_description', ''),
                'optimization_settings': resume_data.get('optimization_settings', {}),
                'generated_at': datetime.now().isoformat()
            }
        )
        db.add(resume_version)
        db.commit()
        db.refresh(resume_version)
        
        # Update pdf_url with the actual resume version ID
        resume_version.pdf_url = f"/api/resume/pdf/{resume_version.id}"
        db.commit()
        
        # Return PDF as response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=resume_{application_id}_{resume_version.id}.pdf"
            }
        )
        
    except LaTeXCompilationError as e:
        logger.error(f"LaTeX compilation failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to design resume: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error designing resume for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while designing the resume"
        )

@router.get("/versions/{application_id}")
def get_resume_versions(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get resume versions for a specific application
    """
    # Verify application belongs to user
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Get resume versions for this application
    resume_versions = db.query(ResumeVersion).filter(
        ResumeVersion.application_id == application_id
    ).order_by(ResumeVersion.created_at.desc()).all()
    
    return {
        "application_id": application_id,
        "resume_versions": [
            {
                "id": version.id,
                "title": version.title,
                "template_used": version.template_used,
                "created_at": version.created_at.isoformat(),
                "pdf_url": version.pdf_url,
                "has_pdf": version.pdf_content is not None and len(version.pdf_content) > 0
            }
            for version in resume_versions
        ]
    }

@router.get("/pdf/{resume_version_id}")
def get_resume_pdf(
    resume_version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get PDF content for a specific resume version
    """
    # Get resume version and verify ownership
    resume_version = db.query(ResumeVersion).filter(
        ResumeVersion.id == resume_version_id,
        ResumeVersion.user_id == current_user.id
    ).first()
    
    if not resume_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume version not found"
        )
    
    if not resume_version.pdf_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF content not available"
        )
    
    # Decode base64 content
    try:
        pdf_content = base64.b64decode(resume_version.pdf_content)
    except Exception as e:
        logger.error(f"Failed to decode PDF content for resume version {resume_version_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decode PDF content"
        )
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=resume_{resume_version_id}.pdf"
        }
    )

@router.get("/templates")
def get_resume_templates(
    current_user: User = Depends(get_current_user)
):
    """
    Get available resume templates
    """
    return {
        "templates": [
            {
                "id": "professional",
                "name": "Professional",
                "description": "Clean, professional layout suitable for most industries"
            },
            {
                "id": "modern",
                "name": "Modern",
                "description": "Contemporary design with emphasis on skills and achievements"
            },
            {
                "id": "academic",
                "name": "Academic",
                "description": "Traditional academic format with publications and research focus"
            }
        ]
    }