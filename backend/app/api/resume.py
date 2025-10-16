"""
Resume generation API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
import logging
from jose import jwt
from app.core.settings import settings
import tempfile
import base64
import traceback
from datetime import datetime
from pathlib import Path
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.application import Application
from app.models.job_posting import JobPosting
from app.models.resume import ResumeVersion
from app.services.latex_service import latex_service, LaTeXCompilationError
from app.services.llm_service import llm_service
from app.services.s3_service import s3_service
from app.services.resume_generation_service import ResumeGenerationService
from app.utils.template_utils import extract_document_content, combine_with_template_preamble
from app.utils.latex_sanitizer import validate_user_latex, LaTeXSecurityError
from app.schemas.resume import ResumeDesignRequest, ResumeDesignResponse, KeywordAnalysisRequest, KeywordAnalysisResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize rate limiter with user ID-based limiting
def get_user_key(request: Request):
    """
    Custom key function for rate limiting that uses user ID when available.
    Falls back to IP address for unauthenticated requests.
    
    This approach extracts the user ID from the JWT token directly since
    rate limiting happens before FastAPI dependency injection.
    """
    try:
        # Try to get Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # No auth token, fall back to IP
            return get_remote_address(request)
        
        # Extract token
        token = auth_header.split(" ")[1]
        
        # Decode JWT token to get user ID        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id:
            return f"user:{user_id}"
        else:
            return get_remote_address(request)
            
    except Exception:
        # If anything fails (invalid token, expired, etc.), fall back to IP
        return get_remote_address(request)

limiter = Limiter(key_func=get_user_key)

@limiter.limit("1/minute")  # Rate limit: max 1 resume designs per minute
@router.post("/design", response_model=ResumeDesignResponse, status_code=status.HTTP_202_ACCEPTED)
async def design_resume(
    request: Request,  # Required for rate limiting
    resume_data: ResumeDesignRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Design an AI-optimized PDF resume from user data and job description
    Creates an application if one doesn't exist and stores resume version
    Returns immediately with resume generation ID, processing happens in background
    """
    logger.info(f"Resume design request received for user {current_user.id}")
    try:
        # Get or create application
        application_id = resume_data.linked_application_id
        if not application_id:
            # Create job posting first
            job_posting = JobPosting(
                title=resume_data.job_title,
                company=resume_data.company,
                description=resume_data.job_description,
                status='manual',
                created_by_user_id=current_user.id,
                provenance={
                    "method": "manual",
                    "extractor": "resume_designer",
                    "confidence": 1.0
                }
            )
            db.add(job_posting)
            db.commit()
            db.refresh(job_posting)
            
            # Create new application linked to job posting
            application = Application(
                user_id=current_user.id,
                job_posting_id=job_posting.id,
                applied_date=datetime.now()
            )
            db.add(application)
            db.commit()
            db.refresh(application)
            application_id = application.id
        else:
            # Verify application belongs to user
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

        # Create resume version record with metadata for background processing
        resume_version = ResumeVersion(
            user_id=current_user.id,
            application_id=application_id,
            title=f"{resume_data.personal_info.name} - {application.job_posting.company if application.job_posting else 'Unknown Company'}",
            template_used='Detailed Resume',
            pdf_url=None,  # Will be set after background processing
            s3_key=None,  # Will be set after background processing
            latex_s3_key=None,  # Will be set after background processing
            resume_metadata={
                'job_title': resume_data.job_title,
                'company': resume_data.company,
                'job_description': resume_data.job_description,
                'personal_info': resume_data.personal_info.model_dump(),
                'locale': resume_data.locale,
                'optimization_settings': {},
                'generated_at': datetime.now().isoformat()
            }
        )
        db.add(resume_version)
        db.commit()
        db.refresh(resume_version)
        
        # Add background task for resume generation
        background_tasks.add_task(
            ResumeGenerationService.process_resume_generation_async,
            str(resume_version.id)
        )
        
        logger.info(
            f"Resume generation initiated for user {current_user.id}, "
            f"resume_version_id={resume_version.id}, application_id={application_id}"
        )
        
        # Return immediately with resume generation ID
        return ResumeDesignResponse(
            resume_generation_id=resume_version.id,
            status="processing",
            message="Resume generation initiated"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error initiating resume generation for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while initiating resume generation"
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
                "has_pdf": version.s3_key is not None
            }
            for version in resume_versions
        ]
    }


@router.get("/pdf/{resume_version_id}/blob")
async def get_resume_pdf_blob(
    resume_version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the PDF blob for a completed resume generation
    """
    # Verify resume version belongs to user
    resume_version = db.query(ResumeVersion).filter(
        ResumeVersion.id == resume_version_id,
        ResumeVersion.user_id == current_user.id
    ).first()
    
    if not resume_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Check if generation is complete
    if not resume_version.pdf_url or not resume_version.s3_key:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Resume generation is still in progress"
        )
    
    try:
        pdf_content = await s3_service.download_pdf(resume_version.s3_key)
        
        if not pdf_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve PDF from storage"
            )
        
        # Create user-friendly filename for download
        filename_parts = []
        if resume_version.title:
            clean_title = "".join(c if c.isalnum() or c in " -" else "" for c in resume_version.title.strip())
            filename_parts.append(clean_title.replace(" ", "_"))
        filename_parts.append(f"v{resume_version.id}")
        
        filename = "_".join(filename_parts) if filename_parts else f"resume_{resume_version.id}"
        filename += ".pdf"
        
        # Return JSON response with PDF data
        return {
            "resume_version_id": resume_version.id,
            "pdf_data": base64.b64encode(pdf_content).decode('utf-8'),
            "filename": filename,
            "content_type": "application/pdf"
        }
        
    except Exception as e:
        logger.error(f"Failed to download resume PDF {resume_version_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resume PDF"
        )


@router.get("/pdf/{resume_version_id}/url")
async def get_resume_pdf_url(
    resume_version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the CloudFront URL for a specific resume version (for frontend to open in new tab)
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
    
    # Check if PDF is stored in S3
    if resume_version.s3_key:
        try:
            # Generate secure CloudFront signed URL (30 minutes expiration)
            pdf_url = await s3_service.get_pdf_url(resume_version.s3_key, expiration=1800)
            if pdf_url:
                # Generate filename on-the-fly (same logic as in /design endpoint)
                filename_parts = ["Resume"]
                
                # Get user name
                user_name = f"{resume_version.user.first_name} {resume_version.user.last_name}"
                clean_name = "".join(c if c.isalnum() or c in " -" else "" for c in user_name.strip())
                filename_parts.append(clean_name.replace(" ", "_"))
                
                # Get job title and company from application
                application = db.query(Application).options(
                    joinedload(Application.job_posting)
                ).filter(Application.id == resume_version.application_id).first()
                if application and application.job_posting:
                    if application.job_posting.title:
                        clean_title = "".join(c if c.isalnum() or c in " -" else "" for c in application.job_posting.title.strip())
                        filename_parts.append(clean_title.replace(" ", "_"))
                    if application.job_posting.company:
                        clean_company = "".join(c if c.isalnum() or c in " -" else "" for c in application.job_posting.company.strip())
                        filename_parts.append(clean_company.replace(" ", "_"))
                
                # Fallback to title if no application data
                if len(filename_parts) == 2 and resume_version.title:
                    clean_title = "".join(c if c.isalnum() or c in " -" else "" for c in resume_version.title.strip())
                    filename_parts.append(clean_title.replace(" ", "_"))
                
                filename = "_".join(filename_parts) if len(filename_parts) > 2 else f"Resume_{resume_version.id}"
                filename += ".pdf"
                
                return {"url": pdf_url, "filename": filename}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate PDF URL"
                )
        except Exception as e:
            logger.error(f"Failed to get PDF URL for resume version {resume_version_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve PDF URL from storage"
            )
    else:
        # No S3 key means this resume was not properly generated
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF content not available - resume may not have been properly generated"
        )


@router.get("/latex/{resume_version_id}")
async def get_resume_latex(
    resume_version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the LaTeX document content (between \\begin{document} and \\end{document}) 
    for a specific resume version
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
    
    # Check if LaTeX is stored in S3
    if resume_version.latex_s3_key:
        try:
            latex_content = await s3_service.get_latex_content(resume_version.latex_s3_key)
            if latex_content:
                # Extract only the document content (between \begin{document} and \end{document})
                try:
                    document_content = extract_document_content(latex_content)
                    return {"latex_content": document_content}
                except ValueError as e:
                    logger.error(f"Failed to extract document content from LaTeX: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="LaTeX content format is invalid"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve LaTeX content from storage"
                )
        except Exception as e:
            logger.error(f"Failed to get LaTeX content for resume version {resume_version_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve LaTeX content from storage"
            )
    else:
        # No LaTeX S3 key means this resume was not properly generated
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LaTeX content not available - resume may not have been properly generated"
        )


@router.put("/latex/{resume_version_id}")
@limiter.limit("2/minute")  # Rate limit: max 2 LaTeX compilations per minute
async def update_resume_latex(
    request: Request,  # Required for rate limiting
    resume_version_id: int,
    latex_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the LaTeX document content (between \\begin{document} and \\end{document}) 
    for a specific resume version and regenerate PDF. The content will be combined 
    with the template preamble automatically.
    
    Security: This endpoint enforces strict validation and rate limiting to prevent
    malicious LaTeX code execution, file system access, and DoS attacks.
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
    
    # Extract LaTeX content from request
    latex_content = latex_data.get("latex_content")
    if not latex_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LaTeX content is required"
        )
    
    # SECURITY: Comprehensive validation and sanitization
    try:
        validate_user_latex(latex_content)
    except LaTeXSecurityError as e:
        logger.warning(
            f"LaTeX security violation detected for user {current_user.id}: {str(e)}",
            extra={'user_id': current_user.id, 'resume_version_id': resume_version_id}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security validation failed: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    try:
        # Combine document content with template preamble to create complete LaTeX
        complete_latex = combine_with_template_preamble(latex_content)
        
        # Compile LaTeX to PDF
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write LaTeX file
            tex_file = temp_path / "resume.tex"
            tex_file.write_text(complete_latex, encoding='utf-8')
            
            # Compile LaTeX to PDF
            pdf_file = latex_service.compile_latex(tex_file, temp_path)
            
            # Read PDF content
            pdf_bytes = pdf_file.read_bytes()
            
            # Upload new PDF and LaTeX to S3
            # Delete old files from S3 if they exist
            if resume_version.s3_key:
                await s3_service.delete_pdf(resume_version.s3_key)
            if resume_version.latex_s3_key:
                await s3_service.delete_latex(resume_version.latex_s3_key)
            
            # Upload new files
            pdf_s3_key = await s3_service.upload_pdf(pdf_bytes, current_user.id, resume_version.id)
            latex_s3_key = await s3_service.upload_latex(complete_latex, current_user.id, resume_version.id)
            
            if pdf_s3_key and latex_s3_key:
                # Update resume version with new S3 keys
                resume_version.s3_key = pdf_s3_key
                resume_version.latex_s3_key = latex_s3_key
                db.commit()
                
                # Create user-friendly filename for download
                filename_parts = []
                if resume_version.title:
                    clean_title = "".join(c if c.isalnum() or c in " -" else "" for c in resume_version.title.strip())
                    filename_parts.append(clean_title.replace(" ", "_"))
                filename_parts.append(f"v{resume_version.id}")
                
                filename = "_".join(filename_parts) if filename_parts else f"resume_{resume_version.id}"
                filename += ".pdf"
                
                return Response(
                    content=pdf_bytes,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}"
                    }
                )
            else:
                # If S3 upload fails, return error
                error_details = []
                if not pdf_s3_key:
                    error_details.append("PDF upload to S3 failed")
                if not latex_s3_key:
                    error_details.append("LaTeX upload to S3 failed")
                
                logger.error(f"S3 upload failed for resume {resume_version.id}: {', '.join(error_details)}")
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to store updated resume content: {', '.join(error_details)}"
                )
                
    except LaTeXCompilationError as e:
        logger.error(f"LaTeX compilation failed for resume version {resume_version_id}: {str(e)}")
        
        # Provide user-friendly error messages
        error_message = str(e)
        if "timed out" in error_message.lower():
            detail = (
                "LaTeX compilation timed out. This usually means your resume is too complex. "
                "Try: (1) Reducing the number of sections, (2) Simplifying formatting, "
                "(3) Removing excessive content. If you believe this is an error, please contact support."
            )
        else:
            detail = f"LaTeX compilation failed: {error_message}"
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
        
    except Exception as e:
        logger.error(f"Unexpected error updating resume LaTeX: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@limiter.limit("2/minute")  # Rate limit: max 2 keyword analysis per minute
@router.post("/analyze-keywords", response_model=KeywordAnalysisResponse)
async def analyze_keywords(
    request: Request,  # Required for rate limiting
    keyword_request: KeywordAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze job description to extract key skills and keywords using LLM
    """
    logger.info(f"Keyword analysis request received for user {current_user.id}")
    
    try:
        # Validate job description
        if not keyword_request.job_description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description cannot be empty"
            )
        
        # Use LLM service to analyze keywords
        logger.debug(f"Starting keyword analysis for user {current_user.id}")
        keywords = await llm_service.analyze_keywords(keyword_request.job_description)
        logger.debug(f"Keyword analysis completed for user {current_user.id}, found {len(keywords)} keywords")
        
        return KeywordAnalysisResponse(keywords=keywords)
        
    except Exception as e:
        logger.error(f"Error in keyword analysis for user {current_user.id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return user-friendly error message
        error_message = str(e)
        if "OpenRouter" in error_message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to analyze keywords. Please try again."
            )