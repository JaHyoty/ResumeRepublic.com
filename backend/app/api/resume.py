"""
Resume generation API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import tempfile
from datetime import datetime
from pathlib import Path

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.application import Application
from app.models.resume import ResumeVersion
from app.models.experience import Experience, ExperienceTitle
from app.models.education import Education
from app.models.skill import Skill
from app.models.certification import Certification
from app.models.publication import Publication
from app.models.project import Project, ProjectTechnology, ProjectAchievement
from app.models.website import Website
from app.services.latex_service import latex_service, LaTeXCompilationError
from app.services.llm_service import llm_service
from app.utils.template_utils import extract_template_content, get_full_template_content
from app.schemas.resume import ResumeDesignRequest

router = APIRouter()
logger = logging.getLogger(__name__)

def fetch_user_data_for_resume(user_id: int, db: Session) -> Dict[str, Any]:
    """
    Fetch all user data needed for resume generation
    """
    logger.debug(f"Fetching user data for user {user_id}")
    try:
        # Fetch experiences with titles
        experiences = db.query(Experience).filter(Experience.user_id == user_id).all()
        logger.debug(f"Found {len(experiences)} experiences for user {user_id}")
    except Exception as e:
        logger.error(f"Error fetching experiences for user {user_id}: {str(e)}")
        raise
    experience_data = []
    for exp in experiences:
        titles = db.query(ExperienceTitle).filter(ExperienceTitle.experience_id == exp.id).all()
        
        experience_data.append({
            "company": exp.company,
            "location": exp.location,
            "start_date": exp.start_date.isoformat() if exp.start_date else None,
            "end_date": exp.end_date.isoformat() if exp.end_date else None,
            "is_current": exp.is_current,
            "description": exp.description,
            "titles": [{"title": t.title, "is_primary": t.is_primary} for t in titles]
        })
    
    # Fetch education
    education = db.query(Education).filter(Education.user_id == user_id).all()
    education_data = []
    for edu in education:
        # Format end date with "Expected" prefix if in the future
        end_date_formatted = None
        if edu.end_date:
            if edu.end_date > datetime.now().date():
                # Future date - add "Expected" prefix
                end_date_formatted = f"Expected {edu.end_date.strftime('%B %Y')}"
            else:
                # Past date - format normally
                end_date_formatted = edu.end_date.strftime('%B %Y')
        
        education_data.append({
            "institution": edu.institution,
            "degree": edu.degree,
            "field_of_study": edu.field_of_study,
            "end_date": end_date_formatted,
            "gpa": edu.gpa,
            "description": edu.description,
            "location": edu.location,
            "website_url": edu.website_url
        })
    
    # Fetch skills
    skills = db.query(Skill).filter(Skill.user_id == user_id).all()
    skills_data = [{"name": skill.name} for skill in skills]
    
    # Fetch certifications
    certifications = db.query(Certification).filter(Certification.user_id == user_id).all()
    certifications_data = []
    for cert in certifications:
        certifications_data.append({
            "name": cert.name,
            "issuer": cert.issuer,
            "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
            "expiry_date": cert.expiry_date.isoformat() if cert.expiry_date else None,
            "credential_id": cert.credential_id,
            "url": cert.credential_url
        })
    
    # Fetch publications
    publications = db.query(Publication).filter(Publication.user_id == user_id).all()
    publications_data = []
    for pub in publications:
        publications_data.append({
            "title": pub.title,
            "co_authors": pub.co_authors,
            "publisher": pub.publisher,
            "publication_date": pub.publication_date.isoformat() if pub.publication_date else None,
            "url": pub.url,
            "description": pub.description
        })
    
    # Fetch projects with technologies and achievements
    projects = db.query(Project).filter(Project.user_id == user_id).all()
    projects_data = []
    for project in projects:
        technologies = db.query(ProjectTechnology).filter(ProjectTechnology.project_id == project.id).all()
        achievements = db.query(ProjectAchievement).filter(ProjectAchievement.project_id == project.id).all()
        
        projects_data.append({
            "name": project.name,
            "description": project.description,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "end_date": project.end_date.isoformat() if project.end_date else None,
            "is_current": project.is_current,
            "url": project.url,
            "technologies": [{"technology": t.technology} for t in technologies],
            "achievements": [{"description": a.description} for a in achievements]
        })
    
    # Fetch websites
    websites = db.query(Website).filter(Website.user_id == user_id).all()
    websites_data = []
    for website in websites:
        websites_data.append({
            "site_name": website.site_name,
            "url": website.url
        })
    
    return {
        "experiences": experience_data,
        "education": education_data,
        "skills": skills_data,
        "certifications": certifications_data,
        "publications": publications_data,
        "projects": projects_data,
        "websites": websites_data
    }

def combine_template_with_content(template_content: str, optimized_content: str) -> str:
    """
    Combine the template preamble (before \begin{document}) with the optimized content
    """
    # Find where \begin{document} starts in the template
    begin_doc_index = template_content.find('\\begin{document}')
    
    if begin_doc_index == -1:
        # If no \begin{document} found, return the optimized content as-is
        return optimized_content
    
    # Extract the preamble (everything before \begin{document})
    preamble = template_content[:begin_doc_index].strip()
    
    # Combine preamble with optimized content
    complete_latex = preamble + '\n\n' + optimized_content
    
    return complete_latex

async def generate_optimized_resume_pdf(resume_data: Dict[str, Any], current_user: User, db: Session) -> tuple[bytes, str]:
    """
    Generate an AI-optimized PDF resume using LLM and LaTeX compilation
    """
    try:
        # Get full template content (including preamble) and content for LLM
        full_template_content = get_full_template_content("ResumeTemplate1.tex")
        template_content_for_llm = extract_template_content("ResumeTemplate1.tex")
        
        # Fetch all user data from database
        user_data = fetch_user_data_for_resume(current_user.id, db)
        
        # Get locale for LLM formatting instructions
        locale = resume_data.get("locale", "en-US")
        personal_info = resume_data.get("personal_info", {})
        
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
        
        # Generate optimized LaTeX using LLM
        job_title = resume_data.get("job_title", "")
        job_description = resume_data.get("job_description", "")
        
        logger.debug(f"Calling LLM service for user {current_user.id}")
        optimized_latex = await llm_service.generate_resume(
            job_title=job_title,
            job_description=job_description,
            applicant_data=applicant_data,
            template_content=template_content_for_llm,
            locale=locale
        )
        logger.debug(f"LLM service completed for user {current_user.id}")
        
        # Combine template preamble with optimized content
        complete_latex = combine_template_with_content(full_template_content, optimized_latex)
        
        # Debug: Log the generated LaTeX content
        logger.debug(f"Generated LaTeX content length: {len(complete_latex)}")
        logger.debug(f"LaTeX content preview: {complete_latex[:500]}...")
        
        # Validate LaTeX content
        if not complete_latex.strip():
            raise Exception("Generated LaTeX content is empty")
        
        if '\\begin{document}' not in complete_latex:
            raise Exception("Generated LaTeX content is missing \\begin{document}")
        
        if '\\end{document}' not in complete_latex:
            raise Exception("Generated LaTeX content is missing \\end{document}")
        
        # Compile LaTeX to PDF using the existing LaTeX service
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write LaTeX file
            tex_file = temp_path / "resume.tex"
            tex_file.write_text(complete_latex, encoding='utf-8')
            
            # Debug: Log the file content
            logger.debug(f"Written LaTeX file size: {tex_file.stat().st_size} bytes")
            
            # Compile LaTeX to PDF
            logger.debug(f"Starting LaTeX compilation for user {current_user.id}")
            pdf_file = latex_service.compile_latex(tex_file, temp_path)
            logger.debug(f"LaTeX compilation completed for user {current_user.id}")
            
            # Read PDF content
            pdf_bytes = pdf_file.read_bytes()
            logger.debug(f"PDF file read successfully, size: {len(pdf_bytes)} bytes")
            return pdf_bytes, complete_latex
            
    except Exception as e:
        logger.error(f"Failed to generate optimized resume: {str(e)}")
        raise LaTeXCompilationError(f"Resume generation failed: {str(e)}")

@router.post("/design")
async def design_resume(
    resume_data: ResumeDesignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Design an AI-optimized PDF resume from user data and job description
    Creates an application if one doesn't exist and stores resume version
    """
    logger.info(f"Resume design request received for user {current_user.id}")
    try:
        # Get or create application
        application_id = resume_data.linked_application_id
        if not application_id:
            # Create new application from job description
            application = Application(
                user_id=current_user.id,
                job_title=resume_data.job_title,
                company=resume_data.company,
                job_description=resume_data.job_description,
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

        # Convert Pydantic model to dict for compatibility
        resume_data_dict = resume_data.model_dump()
        
        # Generate optimized PDF using LLM and LaTeX service
        logger.debug(f"Starting resume generation for user {current_user.id}")
        try:
            pdf_content, latex_content = await generate_optimized_resume_pdf(resume_data_dict, current_user, db)
            logger.debug(f"Resume generation completed for user {current_user.id}, PDF size: {len(pdf_content)} bytes")
        except Exception as e:
            logger.error(f"Error in resume generation for user {current_user.id}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        # Create resume version record first to get the ID
        resume_version = ResumeVersion(
            user_id=current_user.id,
            application_id=application_id,
            title=f"{resume_data.personal_info.name} - {application.company}",
            template_used='Detailed Resume',
            pdf_url=None,  # Will be set after S3 upload
            s3_key=None,  # Will be set after S3 upload
            latex_s3_key=None,  # Will be set after S3 upload
            resume_metadata={
                'job_description': resume_data.job_description,
                'optimization_settings': {},
                'generated_at': datetime.now().isoformat()
            }
        )
        db.add(resume_version)
        db.commit()
        db.refresh(resume_version)
        
        # Upload both PDF and LaTeX to S3
        from app.services.s3_service import s3_service
        
        # Generate user-friendly filename for the PDF
        filename_parts = ["Resume"]
        
        # Get user name
        user_name = f"{current_user.first_name} {current_user.last_name}"
        clean_name = "".join(c if c.isalnum() or c in " -" else "" for c in user_name.strip())
        filename_parts.append(clean_name.replace(" ", "_"))
        
        # Get job title and company from application
        if application:
            if application.job_title:
                clean_title = "".join(c if c.isalnum() or c in " -" else "" for c in application.job_title.strip())
                filename_parts.append(clean_title.replace(" ", "_"))
            if application.company:
                clean_company = "".join(c if c.isalnum() or c in " -" else "" for c in application.company.strip())
                filename_parts.append(clean_company.replace(" ", "_"))
        
        # Fallback to title if no application data
        if len(filename_parts) == 2 and resume_version.title:
            clean_title = "".join(c if c.isalnum() or c in " -" else "" for c in resume_version.title.strip())
            filename_parts.append(clean_title.replace(" ", "_"))
        
        pdf_filename = "_".join(filename_parts) if len(filename_parts) > 2 else f"Resume_{resume_version.id}"
        pdf_filename += ".pdf"
        
        pdf_s3_key = await s3_service.upload_pdf(pdf_content, current_user.id, resume_version.id, filename=pdf_filename)
        latex_s3_key = await s3_service.upload_latex(latex_content, current_user.id, resume_version.id)
        
        if pdf_s3_key and latex_s3_key:
            # Both uploads successful - update with S3 information
            resume_version.s3_key = pdf_s3_key
            resume_version.latex_s3_key = latex_s3_key
            resume_version.pdf_url = f"/api/resume/pdf/{resume_version.id}"  # Keep existing API endpoint
            db.commit()
        else:
            # If S3 upload fails, return error
            error_details = []
            if not pdf_s3_key:
                error_details.append("PDF upload to S3 failed")
            if not latex_s3_key:
                error_details.append("LaTeX upload to S3 failed")
            
            logger.error(f"S3 upload failed for resume {resume_version.id}: {', '.join(error_details)}")
            
            # Clean up the resume version record since we can't store the content
            db.delete(resume_version)
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store resume content: {', '.join(error_details)}"
            )
        
        # Return PDF as response
        logger.debug(f"Returning PDF response, size: {len(pdf_content)} bytes")
        
        # Create user-friendly filename for download
        filename_parts = []
        if resume_version.title:
            clean_title = "".join(c if c.isalnum() or c in " -" else "" for c in resume_version.title.strip())
            filename_parts.append(clean_title.replace(" ", "_"))
        filename_parts.append(f"v{resume_version.id}")
        
        filename = "_".join(filename_parts) if filename_parts else f"resume_{resume_version.id}"
        filename += ".pdf"
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
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
                "has_pdf": version.s3_key is not None
            }
            for version in resume_versions
        ]
    }



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
        from app.services.s3_service import s3_service
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
                application = db.query(Application).filter(Application.id == resume_version.application_id).first()
                if application:
                    if application.job_title:
                        clean_title = "".join(c if c.isalnum() or c in " -" else "" for c in application.job_title.strip())
                        filename_parts.append(clean_title.replace(" ", "_"))
                    if application.company:
                        clean_company = "".join(c if c.isalnum() or c in " -" else "" for c in application.company.strip())
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