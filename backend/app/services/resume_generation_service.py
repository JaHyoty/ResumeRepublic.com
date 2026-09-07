"""
Resume generation service — DynamoDB version.
Handles background resume generation with polling status updates.
"""

import asyncio
import time
import shutil
from typing import Optional, Dict, Any
import structlog
import base64
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from app.core.dynamodb import get_dynamodb_client, DynamoDBClient
from app.core.dynamodb_models import (
    SK_RESUME, SK_APP, SK_JOBPOST, SK_EXP, SK_EXPTITLE,
    SK_EDU, SK_SKILL, SK_CERT, SK_PUB, SK_PROJECT, SK_WEBSITE,
    build_gen_status_item,
)
from app.services.latex_service import latex_service, LaTeXCompilationError
from app.services.llm_service import llm_service
from app.services.s3_service import s3_service
from app.utils.template_utils import extract_template_content, get_full_template_content, combine_with_template_preamble
from app.services.webhook_service import (
    send_entity_update,
    send_entity_completed,
    send_entity_failed,
)

logger = structlog.get_logger()


class ResumeGenerationService:
    """
    Service for handling background resume generation with polling status updates.
    """

    @staticmethod
    async def process_resume_generation_async(resume_generation_id: str):
        """
        Async background task for FastAPI BackgroundTasks.
        Gets its own DynamoDB client.
        """
        db = get_dynamodb_client()
        await ResumeGenerationService.process_resume_generation(resume_generation_id, db)

    @staticmethod
    async def process_resume_generation(resume_generation_id: str, db: DynamoDBClient):
        """
        Background task to process resume generation.
        Implements two-stage pipeline with status updates.
        """
        try:
            logger.info(f"Starting resume generation, resume_generation_id={resume_generation_id}")

            # Find the resume version across all users
            # Since we know the resume_id, we scan for it (small dataset)
            resume_id = int(resume_generation_id)

            # We need to find the resume item. Since the SK encodes app_id, we need
            # to scan user items. For a small dataset, this is fine.
            # The resume_metadata stores user_id, so we can reconstruct.
            # Alternative: store a lookup item RESUME#<id> -> USER#<uid>
            # For now, use a scan with filter
            from boto3.dynamodb.conditions import Attr
            items = db.scan(
                filter_expression=Attr("entity_type").eq("resume_version") & Attr("id").eq(resume_id),
                limit=1,
            )

            if not items:
                logger.error(f"Resume version not found, resume_generation_id={resume_generation_id}")
                return

            rv = items[0]
            user_id = rv["user_id"]
            app_id = rv["application_id"]
            user_pk = f"USER#{user_id}"

            # Get user
            user_data = db.get_item(user_pk, "PROFILE")
            if not user_data:
                logger.error(f"User not found, user_id={user_id}")
                return

            # Get application
            app_data = db.get_item(user_pk, f"{SK_APP}{app_id}")
            if not app_data:
                logger.error(f"Application not found, application_id={app_id}")
                return

            # Get job posting
            jp_id = app_data.get("job_posting_id")
            jp_data = None
            if jp_id:
                jp_data = db.get_item(f"JOBPOST#{jp_id}", SK_JOBPOST)

            # Send status update - Starting optimization
            await asyncio.sleep(0.5)
            await send_entity_update(
                user_id, "resume_generation", str(resume_id), "optimizing",
                {"message": "Optimizing resume content and structure..."},
            )

            # Stage 1: Generate optimized resume using LLM
            logger.info("Stage 1: LLM optimization")
            pdf_content, latex_content = await ResumeGenerationService._generate_optimized_resume_pdf(
                rv, user_data, app_data, jp_data, db,
            )

            # Stage 2: Upload to S3 and finalize
            logger.info("Stage 2: S3 upload and finalization")
            await ResumeGenerationService._upload_and_finalize_resume(
                rv, pdf_content, latex_content, user_data, app_data, jp_data, db,
            )

            # Send completion status
            await send_entity_completed(
                user_id, "resume_generation", str(resume_id),
                {"message": "Resume generation completed successfully!"},
            )

            logger.info(f"Resume generation completed, resume_id={resume_id}")

        except LaTeXCompilationError as e:
            logger.error(f"LaTeX compilation failed: {str(e)}")
            if "rv" in locals() and "user_id" in locals():
                await send_entity_failed(
                    user_id, "resume_generation", str(resume_generation_id),
                    f"Resume compilation failed: {str(e)}",
                )
        except Exception as e:
            logger.error(f"Resume generation failed: {str(e)}")
            if "rv" in locals() and "user_id" in locals():
                await send_entity_failed(
                    user_id, "resume_generation", str(resume_generation_id),
                    f"Resume generation failed: {str(e)}",
                )

    @staticmethod
    async def _generate_optimized_resume_pdf(
        resume_version: dict,
        user: dict,
        application: dict,
        job_posting: Optional[dict],
        db: DynamoDBClient,
    ):
        """Generate an optimized resume PDF using LLM and LaTeX."""
        user_id = user["id"]

        # Get resume metadata
        metadata = resume_version.get("resume_metadata", {})
        personal_info = metadata.get("personal_info", {})
        job_description = metadata.get("job_description", "")
        locale = metadata.get("locale", "en-US")

        # Fetch all user data for resume
        user_data = ResumeGenerationService._fetch_user_data_for_resume(user_id, db)

        # Get template
        template_content = get_full_template_content()

        # Generate optimized resume using LLM
        optimized_latex = await llm_service.generate_optimized_resume(
            user_data=user_data,
            personal_info=personal_info,
            job_description=job_description,
            template_content=template_content,
            locale=locale,
        )

        # Combine with template preamble
        complete_latex = combine_with_template_preamble(optimized_latex)

        # Compile LaTeX to PDF
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False) as tex_file:
            tex_file.write(complete_latex)
            tex_file_path = Path(tex_file.name)

        temp_path = Path(tempfile.mkdtemp())
        try:
            pdf_file = latex_service.compile_latex(tex_file_path, temp_path)
            pdf_content = pdf_file.read_bytes()
            return pdf_content, complete_latex
        finally:
            if tex_file_path.exists():
                tex_file_path.unlink()
            if temp_path.exists():
                shutil.rmtree(temp_path)

    @staticmethod
    async def _upload_and_finalize_resume(
        resume_version: dict,
        pdf_content: bytes,
        latex_content: str,
        user: dict,
        application: dict,
        job_posting: Optional[dict],
        db: DynamoDBClient,
    ):
        """Upload resume to S3 and update DynamoDB record."""
        user_id = user["id"]
        resume_id = resume_version["id"]

        # Generate filename
        user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}"
        clean_name = "".join(c if c.isalnum() or c in " -" else "" for c in user_name.strip())
        filename_parts = ["Resume", clean_name.replace(" ", "_")]

        if job_posting:
            if job_posting.get("title"):
                clean_title = "".join(c if c.isalnum() or c in " -" else "" for c in job_posting["title"].strip())
                filename_parts.append(clean_title.replace(" ", "_"))
            if job_posting.get("company"):
                clean_company = "".join(c if c.isalnum() or c in " -" else "" for c in job_posting["company"].strip())
                filename_parts.append(clean_company.replace(" ", "_"))

        pdf_filename = "_".join(filename_parts) + ".pdf" if len(filename_parts) > 2 else f"Resume_{resume_id}.pdf"

        pdf_s3_key = await s3_service.upload_pdf(pdf_content, user_id, resume_id, filename=pdf_filename)
        latex_s3_key = await s3_service.upload_latex(latex_content, user_id, resume_id)

        if pdf_s3_key and latex_s3_key:
            db.update_item(
                resume_version["PK"],
                resume_version["SK"],
                {
                    "s3_key": pdf_s3_key,
                    "latex_s3_key": latex_s3_key,
                    "pdf_url": f"/api/resume/pdf/{resume_id}",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        else:
            error_details = []
            if not pdf_s3_key:
                error_details.append("PDF upload to S3 failed")
            if not latex_s3_key:
                error_details.append("LaTeX upload to S3 failed")
            raise Exception(f"Failed to store resume content: {', '.join(error_details)}")

    @staticmethod
    def _fetch_user_data_for_resume(user_id: int, db: DynamoDBClient) -> Dict[str, Any]:
        """Fetch all user data needed for resume generation from DynamoDB."""
        pk = f"USER#{user_id}"

        # Fetch experiences
        experiences_raw = db.query(pk, sk_prefix=SK_EXP)
        experiences = [e for e in experiences_raw if e.get("entity_type") == "experience"]

        # Attach titles to experiences
        for exp in experiences:
            exp_id = exp["id"]
            titles = db.query(pk, sk_prefix=f"{SK_EXPTITLE}{exp_id}#")
            exp["titles"] = titles

        education = db.query(pk, sk_prefix=SK_EDU)
        skills = db.query(pk, sk_prefix=SK_SKILL)
        certifications = db.query(pk, sk_prefix=SK_CERT)
        publications = db.query(pk, sk_prefix=SK_PUB)
        projects = db.query(pk, sk_prefix=SK_PROJECT)
        websites = db.query(pk, sk_prefix=SK_WEBSITE)

        return {
            "experiences": [{
                "id": exp.get("id"),
                "company": exp.get("company"),
                "location": exp.get("location"),
                "start_date": exp.get("start_date"),
                "end_date": exp.get("end_date"),
                "is_current": exp.get("is_current"),
                "description": exp.get("description"),
                "titles": [{
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "is_primary": t.get("is_primary"),
                } for t in exp.get("titles", [])],
            } for exp in experiences],
            "education": [{
                "id": e.get("id"),
                "institution": e.get("institution"),
                "degree": e.get("degree"),
                "field_of_study": e.get("field_of_study"),
                "start_date": e.get("start_date"),
                "end_date": e.get("end_date"),
                "gpa": e.get("gpa"),
                "coursework": e.get("coursework"),
            } for e in education],
            "skills": [{"id": s.get("id"), "name": s.get("name")} for s in skills],
            "certifications": [{
                "id": c.get("id"),
                "name": c.get("name"),
                "issuer": c.get("issuer"),
                "issue_date": c.get("issue_date"),
                "expiry_date": c.get("expiry_date"),
                "credential_id": c.get("credential_id"),
                "credential_url": c.get("credential_url"),
            } for c in certifications],
            "publications": [{
                "id": p.get("id"),
                "title": p.get("title"),
                "authors": p.get("authors"),
                "publisher": p.get("publisher"),
                "publication_date": p.get("publication_date"),
                "url": p.get("url"),
                "description": p.get("description"),
                "publication_type": p.get("publication_type"),
            } for p in publications],
            "projects": [{
                "id": p.get("id"),
                "name": p.get("name"),
                "description": p.get("description"),
                "role": p.get("role"),
                "start_date": p.get("start_date"),
                "end_date": p.get("end_date"),
                "is_current": p.get("is_current"),
                "url": p.get("url"),
                "technologies_used": p.get("technologies_used"),
            } for p in projects],
            "websites": [{
                "id": s.get("id"),
                "site_name": s.get("site_name"),
                "url": s.get("url"),
                "created_at": s.get("created_at"),
                "updated_at": s.get("updated_at"),
            } for s in websites],
        }
