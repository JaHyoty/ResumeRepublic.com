"""
Resume generation API endpoints — DynamoDB version
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import Response
import logging
import json
from app.core.settings import settings
import base64
from datetime import datetime, timezone
from app.core.limiter import limiter

from app.core.dynamodb import DynamoDBClient, get_db
from app.core.auth import get_current_user
from app.core.dynamodb_models import (
    UserItem, build_resume_version_item, build_application_item,
    build_job_posting_item, SK_APP, SK_RESUME, SK_JOBPOST,
)
from app.core.lambda_dispatch import invoke_pdf_lambda, invoke_pdf_lambda_sync
from app.services.llm_service import llm_service
from app.services.s3_service import s3_service
from app.utils.template_utils import extract_document_content, combine_with_template_preamble
from app.utils.latex_sanitizer import validate_user_latex, LaTeXSecurityError
from app.schemas.resume import ResumeDesignRequest, ResumeDesignResponse, KeywordAnalysisRequest, KeywordAnalysisResponse

router = APIRouter()
logger = logging.getLogger(__name__)




@router.post("/design", response_model=ResumeDesignResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("1/minute")
async def design_resume(
    request: Request,
    resume_data: ResumeDesignRequest,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Design an AI-optimized PDF resume"""
    logger.info(f"Resume design request received for user {current_user.id}")
    try:
        application_id = resume_data.linked_application_id

        if not application_id:
            # Create job posting
            jp_id = db.next_uuid()
            jp_item = build_job_posting_item(
                job_posting_id=jp_id,
                title=resume_data.job_title,
                company=resume_data.company,
                description=resume_data.job_description,
                status="manual",
                created_by_user_id=current_user.id,
                provenance={"method": "manual", "extractor": "resume_designer", "confidence": 1.0},
            )
            db.put_item(jp_item)

            # Create application
            application_id = db.next_id("application")
            app_item = build_application_item(
                user_id=current_user.id,
                app_id=application_id,
                job_posting_id=jp_id,
                applied_date=datetime.now(timezone.utc).isoformat(),
            )
            db.put_item(app_item)
            company_name = resume_data.company
        else:
            # Verify application belongs to user
            app = db.get_item(f"USER#{current_user.id}", f"{SK_APP}{application_id}")
            if not app:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

            company_name = "Unknown Company"
            jp_id = app.get("job_posting_id")
            if jp_id:
                jp = db.get_item(f"JOBPOST#{jp_id}", SK_JOBPOST)
                if jp:
                    company_name = jp.get("company", "Unknown Company")

        # Create resume version
        resume_id = db.next_id("resume_version")
        rv_item = build_resume_version_item(
            user_id=current_user.id,
            resume_id=resume_id,
            application_id=application_id,
            title=f"{resume_data.personal_info.name} - {company_name}",
            template_used="Detailed Resume",
            resume_metadata={
                "job_title": resume_data.job_title,
                "company": resume_data.company,
                "job_description": resume_data.job_description,
                "personal_info": resume_data.personal_info.model_dump(),
                "locale": resume_data.locale,
                "optimization_settings": {},
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        db.put_item(rv_item)

        # Dispatch to PDF Lambda
        invoke_pdf_lambda(str(resume_id))

        logger.info(f"Resume generation initiated for user {current_user.id}, resume_id={resume_id}")

        return ResumeDesignResponse(
            resume_generation_id=resume_id,
            status="processing",
            message="Resume generation initiated",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating resume generation for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while initiating resume generation",
        )


@router.get("/versions/{application_id}")
def get_resume_versions(
    application_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get resume versions for a specific application"""
    pk = f"USER#{current_user.id}"

    # Verify application exists
    app = db.get_item(pk, f"{SK_APP}{application_id}")
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    versions = db.query(pk, sk_prefix=f"{SK_RESUME}{application_id}#")
    versions.sort(key=lambda v: v.get("created_at") or "", reverse=True)

    # Generate signed URLs for each version
    for v in versions:
        s3_key = v.get("s3_key")
        if s3_key:
            try:
                v["pdf_url"] = s3_service.generate_signed_url(s3_key)
                v["has_pdf"] = True
            except Exception:
                v["pdf_url"] = None
                v["has_pdf"] = False
        else:
            v["has_pdf"] = False

    return {
        "application_id": application_id,
        "resume_versions": versions,
    }


@router.get("/pdf/{resume_version_id}")
async def get_resume_pdf(
    resume_version_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get the PDF for a specific resume version"""
    pk = f"USER#{current_user.id}"

    # Search for the resume version across all applications
    all_resumes = db.query(pk, sk_prefix=SK_RESUME)
    rv = None
    for r in all_resumes:
        if r.get("id") == resume_version_id:
            rv = r
            break

    if not rv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")

    if not rv.get("s3_key"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not available - resume may still be generating",
        )

    # Multi-tenant defense-in-depth: verify key belongs to user
    if not rv["s3_key"].startswith(f"resumes/{current_user.id}/"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        filename = f"resume_{resume_version_id}.pdf"
        signed_url = s3_service.generate_signed_url(rv["s3_key"], filename=filename)
        return {"pdf_url": signed_url, "url": signed_url}
    except Exception as e:
        logger.error(f"Failed to generate signed URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resume PDF",
        )


@router.get("/pdf/{resume_version_id}/url")
async def get_resume_pdf_url(
    resume_version_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get the signed URL for a specific resume version (for frontend to open in new tab)"""
    pk = f"USER#{current_user.id}"
    all_resumes = db.query(pk, sk_prefix=SK_RESUME)
    rv = None
    for r in all_resumes:
        if r.get("id") == resume_version_id:
            rv = r
            break

    if not rv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")

    if not rv.get("s3_key"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not available - resume may still be generating",
        )

    if not rv["s3_key"].startswith(f"resumes/{current_user.id}/"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        filename = f"resume_{resume_version_id}.pdf"
        signed_url = s3_service.generate_signed_url(rv["s3_key"], expiration=1800, filename=filename)
        return {"url": signed_url, "filename": filename}
    except Exception as e:
        logger.error(f"Failed to generate PDF URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resume PDF URL",
        )


@router.get("/pdf/{resume_version_id}/blob")
async def get_resume_pdf_blob(
    resume_version_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get the PDF blob for a completed resume generation"""
    pk = f"USER#{current_user.id}"
    all_resumes = db.query(pk, sk_prefix=SK_RESUME)
    rv = None
    for r in all_resumes:
        if r.get("id") == resume_version_id:
            rv = r
            break

    if not rv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    if not rv.get("s3_key"):
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Resume generation is still in progress",
        )

    if not rv["s3_key"].startswith(f"resumes/{current_user.id}/"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        pdf_content = await s3_service.download_pdf(rv["s3_key"])
        if not pdf_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve PDF from storage",
            )

        filename = f"resume_{resume_version_id}.pdf"
        return {
            "resume_version_id": resume_version_id,
            "pdf_data": base64.b64encode(pdf_content).decode("utf-8"),
            "filename": filename,
            "content_type": "application/pdf",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download resume PDF {resume_version_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resume PDF",
        )


@router.get("/latex/{resume_version_id}")
async def get_resume_latex(
    resume_version_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get the LaTeX source for a specific resume version"""
    pk = f"USER#{current_user.id}"
    all_resumes = db.query(pk, sk_prefix=SK_RESUME)
    rv = None
    for r in all_resumes:
        if r.get("id") == resume_version_id:
            rv = r
            break

    if not rv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")

    if not rv.get("latex_s3_key"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LaTeX content not available",
        )

    if not rv["latex_s3_key"].startswith(f"resumes/{current_user.id}/"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        latex_content = await s3_service.get_latex_content(rv["latex_s3_key"])
        if not latex_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LaTeX content not available",
            )
        document_content = extract_document_content(latex_content)
        return {"latex_content": document_content, "full_latex": latex_content}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve LaTeX: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve LaTeX content",
        )


@router.put("/latex/{resume_version_id}")
@limiter.limit("2/minute")
async def update_resume_latex(
    request: Request,
    resume_version_id: int,
    latex_data: dict,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Update LaTeX and regenerate PDF"""
    pk = f"USER#{current_user.id}"
    all_resumes = db.query(pk, sk_prefix=SK_RESUME)
    rv = None
    for r in all_resumes:
        if r.get("id") == resume_version_id:
            rv = r
            break

    if not rv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume version not found")

    latex_content = latex_data.get("latex_content")
    if not latex_content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="LaTeX content is required")

    try:
        validate_user_latex(latex_content)
    except LaTeXSecurityError as e:
        logger.warning(f"LaTeX security validation failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LaTeX content contains disallowed commands or packages",
        )

    try:
        complete_latex = combine_with_template_preamble(latex_content)

        # Delete old S3 files
        if rv.get("s3_key"):
            await s3_service.delete_pdf(rv["s3_key"])
        if rv.get("latex_s3_key"):
            await s3_service.delete_latex(rv["latex_s3_key"])

        # Dispatch LaTeX compilation to PDF Lambda
        result = invoke_pdf_lambda_sync({
            "action": "compile_latex",
            "latex_content": complete_latex,
            "user_id": current_user.id,
            "resume_version_id": resume_version_id,
        })

        body = json.loads(result.get("body", "{}"))
        if result.get("statusCode") == 400:
            logger.warning(f"LaTeX compilation error for user {current_user.id}: {body.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LaTeX compilation failed. Please check document syntax and structure.",
            )

        pdf_s3_key = body.get("pdf_s3_key")
        latex_s3_key = body.get("latex_s3_key")
        pdf_base64 = body.get("pdf_base64")

        if pdf_s3_key and latex_s3_key:
            db.update_item(rv["PK"], rv["SK"], {
                "s3_key": pdf_s3_key,
                "latex_s3_key": latex_s3_key,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })

            pdf_bytes = base64.b64decode(pdf_base64)
            filename = f"resume_{resume_version_id}.pdf"
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store updated resume content",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating resume LaTeX: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/analyze-keywords", response_model=KeywordAnalysisResponse)
@limiter.limit("2/minute")
async def analyze_keywords(
    request: Request,
    keyword_request: KeywordAnalysisRequest,
    current_user: UserItem = Depends(get_current_user),
):
    """Analyze job description to extract key skills and keywords"""
    try:
        if not keyword_request.job_description.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description cannot be empty")

        keywords = await llm_service.analyze_keywords(keyword_request.job_description)
        return KeywordAnalysisResponse(keywords=keywords)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in keyword analysis: {str(e)}")
        error_message = str(e)
        if "OpenRouter" in error_message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is currently unavailable. Please try again later.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze keywords. Please try again.",
        )
