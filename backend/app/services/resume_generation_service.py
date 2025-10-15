"""
Resume generation service
Handles background resume generation with webhook notifications
"""

import asyncio
import time
import shutil
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
import structlog
import base64
import tempfile
from datetime import datetime
from pathlib import Path

from app.core.database import get_db_for_background_task
from app.models.user import User
from app.models.application import Application
from app.models.job_posting import JobPosting
from app.models.resume import ResumeVersion
from app.models.experience import Experience, ExperienceTitle
from app.models.education import Education
from app.models.skill import Skill
from app.models.certification import Certification
from app.models.publication import Publication
from app.models.project import Project
from app.models.website import Website
from app.services.latex_service import latex_service, LaTeXCompilationError
from app.services.llm_service import llm_service
from app.services.s3_service import s3_service
from app.utils.template_utils import extract_template_content, get_full_template_content, combine_with_template_preamble
from app.api.webhooks import (
    send_entity_update,
    send_entity_completed,
    send_entity_failed
)

logger = structlog.get_logger()


class ResumeGenerationService:
    """
    Service for handling background resume generation with webhook notifications
    """
    
    def __init__(self):
        pass
    
    @staticmethod
    async def process_resume_generation_async(resume_generation_id: str):
        """
        Async background task for FastAPI BackgroundTasks
        Creates its own database session
        """
        with get_db_for_background_task() as db:
            await ResumeGenerationService.process_resume_generation(resume_generation_id, db)
    
    @staticmethod
    async def process_resume_generation(resume_generation_id: str, db: Session):
        """
        Background task to process resume generation
        Implements two-stage pipeline with webhook notifications
        """
        try:
            logger.info(f"Starting resume generation, resume_generation_id={resume_generation_id}")
            
            # Get resume version record
            resume_version = db.query(ResumeVersion).filter(ResumeVersion.id == resume_generation_id).first()
            if not resume_version:
                logger.error(f"Resume version not found, resume_generation_id={resume_generation_id}")
                return
            
            # Get user and application data
            user = db.query(User).filter(User.id == resume_version.user_id).first()
            if not user:
                logger.error(f"User not found, user_id={resume_version.user_id}")
                return
            
            application = db.query(Application).options(
                joinedload(Application.job_posting)
            ).filter(Application.id == resume_version.application_id).first()
            
            if not application:
                logger.error(f"Application not found, application_id={resume_version.application_id}")
                return
            
            # Send webhook notification - Starting optimization
            # Add small delay to ensure frontend has time to subscribe
            await asyncio.sleep(0.5)
            logger.info(f"Sending optimizing webhook for user {user.id}, resume_version {resume_version.id}")
            await send_entity_update(
                user.id,
                'resume_generation',
                str(resume_version.id),
                'optimizing',
                {'message': 'Optimizing resume content and structure...'}
            )
            logger.info(f"Optimizing webhook sent for user {user.id}, resume_version {resume_version.id}")
            
            # Stage 1: Generate optimized resume using LLM
            logger.info("Starting resume generation - Stage 1: LLM optimization")
            pdf_content, latex_content = await ResumeGenerationService._generate_optimized_resume_pdf(
                resume_version, user, application, db
            )
            
            # Stage 2: Upload to S3 and finalize
            logger.info("Starting resume generation - Stage 2: S3 upload and finalization")
            await ResumeGenerationService._upload_and_finalize_resume(
                resume_version, pdf_content, latex_content, user, application, db
            )
            
            # Send completion webhook
            logger.info(f"Sending completion webhook for user {user.id}, resume_version {resume_version.id}")
            await send_entity_completed(
                user.id,
                'resume_generation',
                str(resume_version.id),
                {
                    'message': 'Resume generation completed successfully!'
                }
            )
            logger.info(f"Completion webhook sent for user {user.id}, resume_version {resume_version.id}")
            
            logger.info(f"Resume generation completed successfully, resume_generation_id={resume_generation_id}")
            
        except Exception as e:
            logger.error(f"Resume generation failed, resume_generation_id={resume_generation_id}, error={str(e)}")
            
            # Send failure webhook
            if resume_version and resume_version.user_id:
                await send_entity_failed(
                    resume_version.user_id,
                    'resume_generation',
                    str(resume_version.id),
                    str(e)
                )
    
    @staticmethod
    async def _generate_optimized_resume_pdf(
        resume_version: ResumeVersion, 
        user: User, 
        application: Application, 
        db: Session
    ) -> tuple[bytes, str]:
        """
        Generate an AI-optimized PDF resume using LLM and LaTeX compilation
        """
        try:
            # Get full template content (including preamble) and content for LLM
            full_template_content = get_full_template_content("ResumeTemplate1.tex")
            template_content_for_llm = extract_template_content("ResumeTemplate1.tex")
            
            # Fetch all user data from database
            user_data = ResumeGenerationService._fetch_user_data_for_resume(user.id, db)
            
            # Get locale for LLM formatting instructions
            locale = resume_version.resume_metadata.get("locale", "en-US")
            personal_info = resume_version.resume_metadata.get("personal_info", {})
            
            # Prepare applicant data (combine user data with personal info from UI)
            applicant_data = {
                "personal_info": personal_info,
                "education": user_data["education"],
                "experiences": user_data["experiences"],
                "projects": user_data["projects"],
                "skills": user_data["skills"],
                "certifications": user_data["certifications"],
                "publications": user_data["publications"],
                "websites": user_data["websites"]
            }
            
            # Generate optimized LaTeX using LLM - Stage 1: Initial generation
            job_title = resume_version.resume_metadata.get("job_title", "")
            job_description = resume_version.resume_metadata.get("job_description", "")
            
            logger.debug(f"Calling LLM service Stage 1 for user {user.id}")
            initial_latex = await llm_service._generate_initial_resume(
                job_title=job_title,
                job_description=job_description,
                applicant_knowledge=applicant_data,
                template_content=template_content_for_llm,
                locale=locale
            )
            logger.debug(f"LLM service Stage 1 completed for user {user.id}")
            
            # Send webhook notification - Performing final checks
            logger.info(f"Sending finalizing webhook for user {user.id}, resume_version {resume_version.id}")
            await send_entity_update(
                user.id,
                'resume_generation',
                str(resume_version.id),
                'finalizing',
                {'message': 'Performing final checks and compilation...'}
            )
            logger.info(f"Finalizing webhook sent for user {user.id}, resume_version {resume_version.id}")
            
            # Stage 2: Verify and correct resume
            logger.debug(f"Calling LLM service Stage 2 for user {user.id}")
            verified_latex = await llm_service._verify_and_correct_resume(
                initial_latex,
                applicant_data,
                job_title,
                job_description,
                1  # Assume 1 page for now
            )
            logger.debug(f"LLM service Stage 2 completed for user {user.id}")
            
            # Clean up LaTeX formatting issues
            optimized_latex = llm_service._clean_latex_content(verified_latex)
            
            # Combine template preamble with optimized content
            complete_latex = combine_with_template_preamble(optimized_latex)
            
            # Compile LaTeX to PDF
            logger.debug(f"Compiling LaTeX for user {user.id}")
            
            # Create temporary file for LaTeX content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as tex_file:
                tex_file.write(complete_latex)
                tex_file_path = Path(tex_file.name)
            
            # Create temporary directory for output
            temp_path = Path(tempfile.mkdtemp())
            
            try:
                # Compile LaTeX to PDF
                pdf_file = latex_service.compile_latex(tex_file_path, temp_path)
                
                # Read PDF content
                pdf_content = pdf_file.read_bytes()
                logger.debug(f"LaTeX compilation completed for user {user.id}, PDF size: {len(pdf_content)} bytes")
                
                return pdf_content, complete_latex
                
            finally:
                # Clean up temporary files
                if tex_file_path.exists():
                    tex_file_path.unlink()
                if temp_path.exists():
                    shutil.rmtree(temp_path)
            
        except Exception as e:
            logger.error(f"Error in resume generation for user {user.id}: {str(e)}")
            raise LaTeXCompilationError(f"Resume generation failed: {str(e)}")
    
    @staticmethod
    async def _upload_and_finalize_resume(
        resume_version: ResumeVersion,
        pdf_content: bytes,
        latex_content: str,
        user: User,
        application: Application,
        db: Session
    ):
        """
        Upload resume content to S3 and finalize the resume version
        """
        
        # Generate user-friendly filename for the PDF
        filename_parts = ["Resume"]
        
        # Get user name
        user_name = f"{user.first_name} {user.last_name}"
        clean_name = "".join(c if c.isalnum() or c in " -" else "" for c in user_name.strip())
        filename_parts.append(clean_name.replace(" ", "_"))
        
        # Get job title and company from application
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
        
        pdf_filename = "_".join(filename_parts) if len(filename_parts) > 2 else f"Resume_{resume_version.id}"
        pdf_filename += ".pdf"
        
        pdf_s3_key = await s3_service.upload_pdf(pdf_content, user.id, resume_version.id, filename=pdf_filename)
        latex_s3_key = await s3_service.upload_latex(latex_content, user.id, resume_version.id)
        
        if pdf_s3_key and latex_s3_key:
            # Both uploads successful - update with S3 information
            resume_version.s3_key = pdf_s3_key
            resume_version.latex_s3_key = latex_s3_key
            resume_version.pdf_url = f"/api/resume/pdf/{resume_version.id}"
            db.commit()
        else:
            # If S3 upload fails, raise error
            error_details = []
            if not pdf_s3_key:
                error_details.append("PDF upload to S3 failed")
            if not latex_s3_key:
                error_details.append("LaTeX upload to S3 failed")
            
            logger.error(f"S3 upload failed for resume {resume_version.id}: {', '.join(error_details)}")
            raise Exception(f"Failed to store resume content: {', '.join(error_details)}")
    
    @staticmethod
    def _fetch_user_data_for_resume(user_id: int, db: Session) -> Dict[str, Any]:
        """
        Fetch all user data needed for resume generation
        """
        
        # Fetch experiences with titles
        experiences = db.query(Experience).options(
            joinedload(Experience.titles)
        ).filter(Experience.user_id == user_id).all()
        
        # Convert to dict format
        experiences_data = []
        for exp in experiences:
            exp_data = {
                "id": exp.id,
                "company": exp.company,
                "location": exp.location,
                "start_date": exp.start_date.isoformat() if exp.start_date else None,
                "end_date": exp.end_date.isoformat() if exp.end_date else None,
                "is_current": exp.is_current,
                "description": exp.description,
                "titles": []
            }
            
            for title in exp.titles:
                title_data = {
                    "id": title.id,
                    "title": title.title,
                    "is_primary": title.is_primary
                }
                exp_data["titles"].append(title_data)
            
            experiences_data.append(exp_data)
        
        # Fetch other data
        education = db.query(Education).filter(Education.user_id == user_id).all()
        skills = db.query(Skill).filter(Skill.user_id == user_id).all()
        certifications = db.query(Certification).filter(Certification.user_id == user_id).all()
        publications = db.query(Publication).filter(Publication.user_id == user_id).all()
        projects = db.query(Project).filter(Project.user_id == user_id).all()
        websites = db.query(Website).filter(Website.user_id == user_id).all()
        
        return {
            "experiences": experiences_data,
            "education": [{
                "id": edu.id,
                "institution": edu.institution,
                "degree": edu.degree,
                "field_of_study": edu.field_of_study,
                "start_date": edu.start_date.isoformat() if edu.start_date else None,
                "end_date": edu.end_date.isoformat() if edu.end_date else None,
                "gpa": edu.gpa,
                "description": edu.description,
                "location": edu.location,
                "website_url": edu.website_url
            } for edu in education],
            "skills": [{
                "id": skill.id,
                "name": skill.name,
                "proficiency": skill.proficiency,
                "years_experience": float(skill.years_experience) if skill.years_experience else None,
                "source": skill.source
            } for skill in skills],
            "certifications": [{
                "id": cert.id,
                "name": cert.name,
                "issuer": cert.issuer,
                "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
                "expiry_date": cert.expiry_date.isoformat() if cert.expiry_date else None,
                "credential_id": cert.credential_id,
                "credential_url": cert.credential_url
            } for cert in certifications],
            "publications": [{
                "id": pub.id,
                "title": pub.title,
                "co_authors": pub.co_authors,
                "publisher": pub.publisher,
                "publication_date": pub.publication_date.isoformat() if pub.publication_date else None,
                "url": pub.url,
                "description": pub.description,
                "publication_type": pub.publication_type
            } for pub in publications],
            "projects": [{
                "id": proj.id,
                "name": proj.name,
                "description": proj.description,
                "start_date": proj.start_date.isoformat() if proj.start_date else None,
                "end_date": proj.end_date.isoformat() if proj.end_date else None,
                "is_current": proj.is_current,
                "url": proj.url,
                "technologies_used": proj.technologies_used
            } for proj in projects],
            "websites": [{
                "id": site.id,
                "site_name": site.site_name,
                "url": site.url,
                "created_at": site.created_at.isoformat() if site.created_at else None,
                "updated_at": site.updated_at.isoformat() if site.updated_at else None
            } for site in websites]
        }
