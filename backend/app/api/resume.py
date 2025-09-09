"""
Resume generation API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
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
    """
    try:
        # Generate optimized PDF using LLM and LaTeX service
        pdf_content = latex_service.generate_optimized_resume_pdf(resume_data)
        
        # Return PDF as response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=resume_{current_user.id}.pdf"
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