"""
Experience and Skills Catalog API routes
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import case, desc, nullslast

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.experience import Experience as ExperienceModel, ExperienceTitle as ExperienceTitleModel
from app.models.skill import Skill as SkillModel
from app.models.certification import Certification as CertificationModel
from app.models.publication import Publication as PublicationModel
from app.models.education import Education as EducationModel
from app.models.website import Website as WebsiteModel
from app.models.project import Project as ProjectModel, ProjectTechnology as ProjectTechnologyModel, ProjectAchievement as ProjectAchievementModel
from app.schemas.experience import Experience, ExperienceCreate, ExperienceUpdate
from app.schemas.skill import Skill, SkillCreate, SkillUpdate
from app.schemas.certification import Certification, CertificationCreate, CertificationUpdate
from app.schemas.publication import Publication, PublicationCreate, PublicationUpdate
from app.schemas.education import Education, EducationCreate, EducationUpdate
from app.schemas.website import Website, WebsiteCreate, WebsiteUpdate
from app.schemas.project import Project, ProjectCreate, ProjectUpdate

router = APIRouter()


@router.get("/experiences", response_model=List[Experience])
def get_user_experiences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all experiences for the current user, sorted by end date descending (most recent first)"""
    
    experiences = db.query(ExperienceModel).filter(
        ExperienceModel.user_id == current_user.id
    ).order_by(
        # Sort by end_date descending, but put current positions (is_current=True) at the top
        case(
            (ExperienceModel.is_current == True, 0),
            else_=1
        ),
        # Then sort by end_date descending (most recent first)
        # Use nullslast to put experiences without end_date (current positions) at the top
        nullslast(desc(ExperienceModel.end_date)),
        # Finally sort by start_date descending as a tiebreaker
        desc(ExperienceModel.start_date)
    ).all()
    return experiences


@router.post("/experiences", response_model=Experience, status_code=status.HTTP_201_CREATED)
def create_experience(
    experience_data: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new work experience"""
    # Create the main experience record
    db_experience = ExperienceModel(
        user_id=current_user.id,
        company=experience_data.company,
        location=experience_data.location,
        start_date=experience_data.start_date,
        end_date=experience_data.end_date,
        description=experience_data.description,
        is_current=experience_data.is_current
    )
    
    db.add(db_experience)
    db.flush()  # Flush to get the ID
    
    # Add titles
    for title_data in experience_data.titles:
        db_title = ExperienceTitleModel(
            experience_id=db_experience.id,
            title=title_data.title,
            is_primary=title_data.is_primary
        )
        db.add(db_title)
    
    
    db.commit()
    db.refresh(db_experience)
    return db_experience


@router.get("/experiences/{experience_id}", response_model=Experience)
def get_experience(
    experience_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific experience by ID"""
    experience = db.query(ExperienceModel).filter(
        ExperienceModel.id == experience_id,
        ExperienceModel.user_id == current_user.id
    ).first()
    
    if not experience:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found"
        )
    
    return experience


@router.put("/experiences/{experience_id}", response_model=Experience)
def update_experience(
    experience_id: int,
    experience_data: ExperienceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing experience"""
    experience = db.query(ExperienceModel).filter(
        ExperienceModel.id == experience_id,
        ExperienceModel.user_id == current_user.id
    ).first()
    
    if not experience:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found"
        )
    
    # Update main experience fields if provided
    update_data = experience_data.model_dump(exclude_unset=True, exclude={'titles'})
    for field, value in update_data.items():
        setattr(experience, field, value)
    
    # Update titles if provided
    if hasattr(experience_data, 'titles') and experience_data.titles is not None:
        # Delete existing titles
        db.query(ExperienceTitleModel).filter(
            ExperienceTitleModel.experience_id == experience_id
        ).delete()
        
        # Add new titles
        for title_data in experience_data.titles:
            db_title = ExperienceTitleModel(
                experience_id=experience_id,
                title=title_data.title,
                is_primary=title_data.is_primary
            )
            db.add(db_title)
    
    
    db.commit()
    db.refresh(experience)
    return experience


@router.delete("/experiences/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experience(
    experience_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an experience"""
    experience = db.query(ExperienceModel).filter(
        ExperienceModel.id == experience_id,
        ExperienceModel.user_id == current_user.id
    ).first()
    
    if not experience:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found"
        )
    
    db.delete(experience)
    db.commit()
    return None


# Skills endpoints
@router.get("/skills", response_model=List[Skill])
def get_user_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all skills for the current user, sorted by category and name"""
    skills = db.query(SkillModel).filter(
        SkillModel.user_id == current_user.id
    ).order_by(
        SkillModel.source,
        SkillModel.name
    ).all()
    return skills


@router.post("/skills", response_model=Skill)
def create_skill(
    skill: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new skill for the current user"""
    db_skill = SkillModel(
        **skill.dict(),
        user_id=current_user.id
    )
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return db_skill


@router.get("/skills/{skill_id}", response_model=Skill)
def get_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific skill by ID"""
    skill = db.query(SkillModel).filter(
        SkillModel.id == skill_id,
        SkillModel.user_id == current_user.id
    ).first()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    return skill


@router.put("/skills/{skill_id}", response_model=Skill)
def update_skill(
    skill_id: int,
    skill_update: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a skill"""
    skill = db.query(SkillModel).filter(
        SkillModel.id == skill_id,
        SkillModel.user_id == current_user.id
    ).first()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    # Update only provided fields
    update_data = skill_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(skill, field, value)
    
    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/skills/{skill_id}")
def delete_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a skill"""
    skill = db.query(SkillModel).filter(
        SkillModel.id == skill_id,
        SkillModel.user_id == current_user.id
    ).first()
    
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    db.delete(skill)
    db.commit()
    
    return {"message": "Skill deleted successfully"}


@router.post("/skills/bulk", response_model=List[Skill])
def create_skills_bulk(
    skill_names: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple skills at once from a list of skill names"""
    
    if not skill_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No skill names provided"
        )
    
    # Get existing skill names for the user to avoid duplicates
    existing_skills = db.query(SkillModel).filter(
        SkillModel.user_id == current_user.id
    ).all()
    existing_skill_names = {skill.name.lower() for skill in existing_skills}
    
    # Filter out duplicates and empty names
    new_skills = []
    for skill_name in skill_names:
        skill_name = skill_name.strip()
        if skill_name and skill_name.lower() not in existing_skill_names:
            new_skills.append(SkillModel(
                user_id=current_user.id,
                name=skill_name,
                source="job_analysis"  # Mark these as coming from keyword analysis
            ))
            existing_skill_names.add(skill_name.lower())  # Prevent duplicates within the same request
    
    if not new_skills:
        # If no new skills to add, return empty list
        return []
    
    # Add all new skills to database
    db.add_all(new_skills)
    db.commit()
    
    # Refresh all new skills to get their IDs
    for skill in new_skills:
        db.refresh(skill)
    
    return new_skills


# Certifications endpoints
@router.get("/certifications", response_model=List[Certification])
def get_user_certifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all certifications for the current user, sorted by issue date descending"""
    certifications = db.query(CertificationModel).filter(
        CertificationModel.user_id == current_user.id
    ).order_by(
        desc(CertificationModel.issue_date)
    ).all()
    return certifications


@router.post("/certifications", response_model=Certification)
def create_certification(
    certification: CertificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new certification for the current user"""
    db_certification = CertificationModel(
        **certification.dict(),
        user_id=current_user.id
    )
    db.add(db_certification)
    db.commit()
    db.refresh(db_certification)
    return db_certification


@router.get("/certifications/{certification_id}", response_model=Certification)
def get_certification(
    certification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific certification by ID"""
    certification = db.query(CertificationModel).filter(
        CertificationModel.id == certification_id,
        CertificationModel.user_id == current_user.id
    ).first()
    
    if not certification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )
    
    return certification


@router.put("/certifications/{certification_id}", response_model=Certification)
def update_certification(
    certification_id: int,
    certification_update: CertificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a certification"""
    certification = db.query(CertificationModel).filter(
        CertificationModel.id == certification_id,
        CertificationModel.user_id == current_user.id
    ).first()
    
    if not certification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )
    
    # Update only provided fields
    update_data = certification_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(certification, field, value)
    
    db.commit()
    db.refresh(certification)
    return certification


@router.delete("/certifications/{certification_id}")
def delete_certification(
    certification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a certification"""
    certification = db.query(CertificationModel).filter(
        CertificationModel.id == certification_id,
        CertificationModel.user_id == current_user.id
    ).first()
    
    if not certification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )
    
    db.delete(certification)
    db.commit()
    
    return {"message": "Certification deleted successfully"}


# Publications endpoints
@router.get("/publications", response_model=List[Publication])
def get_user_publications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all publications for the current user, sorted by publication date descending"""
    publications = db.query(PublicationModel).filter(
        PublicationModel.user_id == current_user.id
    ).order_by(
        desc(PublicationModel.publication_date)
    ).all()
    return publications


@router.post("/publications", response_model=Publication)
def create_publication(
    publication: PublicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new publication for the current user"""
    db_publication = PublicationModel(
        **publication.dict(),
        user_id=current_user.id
    )
    db.add(db_publication)
    db.commit()
    db.refresh(db_publication)
    return db_publication


@router.get("/publications/{publication_id}", response_model=Publication)
def get_publication(
    publication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific publication by ID"""
    publication = db.query(PublicationModel).filter(
        PublicationModel.id == publication_id,
        PublicationModel.user_id == current_user.id
    ).first()
    
    if not publication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publication not found"
        )
    
    return publication


@router.put("/publications/{publication_id}", response_model=Publication)
def update_publication(
    publication_id: int,
    publication_update: PublicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a publication"""
    publication = db.query(PublicationModel).filter(
        PublicationModel.id == publication_id,
        PublicationModel.user_id == current_user.id
    ).first()
    
    if not publication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publication not found"
        )
    
    # Update only provided fields
    update_data = publication_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(publication, field, value)
    
    db.commit()
    db.refresh(publication)
    return publication


@router.delete("/publications/{publication_id}")
def delete_publication(
    publication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a publication"""
    publication = db.query(PublicationModel).filter(
        PublicationModel.id == publication_id,
        PublicationModel.user_id == current_user.id
    ).first()
    
    if not publication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publication not found"
        )
    
    db.delete(publication)
    db.commit()
    
    return {"message": "Publication deleted successfully"}


# Education endpoints
@router.get("/education", response_model=List[Education])
def get_education(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all education entries for the current user"""
    education = db.query(EducationModel).filter(
        EducationModel.user_id == current_user.id
    ).order_by(EducationModel.start_date.desc()).all()
    
    return education


@router.post("/education", response_model=Education)
def create_education(
    education_data: EducationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new education entry"""
    education = EducationModel(
        user_id=current_user.id,
        **education_data.model_dump()
    )
    
    db.add(education)
    db.commit()
    db.refresh(education)
    
    return education


@router.put("/education/{education_id}", response_model=Education)
def update_education(
    education_id: int,
    education_data: EducationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an education entry"""
    education = db.query(EducationModel).filter(
        EducationModel.id == education_id,
        EducationModel.user_id == current_user.id
    ).first()
    
    if not education:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education entry not found"
        )
    
    # Update provided fields, including those explicitly set to None (to clear them)
    update_data = education_data.model_dump(exclude_unset=True, exclude_none=False)
    for field, value in update_data.items():
        setattr(education, field, value)
    
    db.commit()
    db.refresh(education)
    
    return education


@router.delete("/education/{education_id}")
def delete_education(
    education_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an education entry"""
    education = db.query(EducationModel).filter(
        EducationModel.id == education_id,
        EducationModel.user_id == current_user.id
    ).first()
    
    if not education:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education entry not found"
        )
    
    db.delete(education)
    db.commit()
    
    return {"message": "Education entry deleted successfully"}


# Website endpoints
@router.get("/websites", response_model=List[Website])
def get_user_websites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all websites for the current user"""
    websites = db.query(WebsiteModel).filter(
        WebsiteModel.user_id == current_user.id
    ).order_by(WebsiteModel.created_at.desc()).all()
    
    return websites


@router.post("/websites", response_model=Website)
def create_website(
    website_data: WebsiteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new website entry"""
    website = WebsiteModel(
        user_id=current_user.id,
        site_name=website_data.site_name,
        url=str(website_data.url)
    )
    
    db.add(website)
    db.commit()
    db.refresh(website)
    
    return website


@router.put("/websites/{website_id}", response_model=Website)
def update_website(
    website_id: int,
    website_data: WebsiteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a website entry"""
    website = db.query(WebsiteModel).filter(
        WebsiteModel.id == website_id,
        WebsiteModel.user_id == current_user.id
    ).first()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    # Update fields if provided
    if website_data.site_name is not None:
        website.site_name = website_data.site_name
    if website_data.url is not None:
        website.url = str(website_data.url)
    
    db.commit()
    db.refresh(website)
    
    return website


@router.delete("/websites/{website_id}")
def delete_website(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a website entry"""
    website = db.query(WebsiteModel).filter(
        WebsiteModel.id == website_id,
        WebsiteModel.user_id == current_user.id
    ).first()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found"
        )
    
    db.delete(website)
    db.commit()
    
    return {"message": "Website deleted successfully"}


# Project endpoints
@router.get("/projects", response_model=List[Project])
def get_user_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all projects for the current user, sorted by end date descending (most recent first)"""
    projects = db.query(ProjectModel).filter(
        ProjectModel.user_id == current_user.id
    ).order_by(
        # Sort by end_date descending, but put current projects (is_current=True) at the top
        case(
            (ProjectModel.is_current == True, 0),
            else_=1
        ),
        # Then sort by end_date descending (most recent first)
        # Use nullslast to put projects without end_date (current projects) at the top
        nullslast(desc(ProjectModel.end_date)),
        # Finally sort by start_date descending as a tiebreaker
        desc(ProjectModel.start_date)
    ).all()
    return projects


@router.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    # Create the main project record
    db_project = ProjectModel(
        user_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
        start_date=project_data.start_date,
        end_date=project_data.end_date,
        url=project_data.url,
        is_current=project_data.is_current
    )
    
    db.add(db_project)
    db.flush()  # Flush to get the ID
    
    # Add technologies
    for tech_data in project_data.technologies:
        db_tech = ProjectTechnologyModel(
            project_id=db_project.id,
            technology=tech_data.technology
        )
        db.add(db_tech)
    
    # Add achievements
    for achievement_data in project_data.achievements:
        db_achievement = ProjectAchievementModel(
            project_id=db_project.id,
            description=achievement_data.description
        )
        db.add(db_achievement)
    
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/projects/{project_id}", response_model=Project)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific project by ID"""
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.put("/projects/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing project"""
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update main project fields if provided
    update_data = project_data.model_dump(exclude_unset=True, exclude={'technologies', 'achievements'})
    for field, value in update_data.items():
        setattr(project, field, value)
    
    # Update technologies if provided
    if hasattr(project_data, 'technologies') and project_data.technologies is not None:
        # Delete existing technologies
        db.query(ProjectTechnologyModel).filter(
            ProjectTechnologyModel.project_id == project_id
        ).delete()
        
        # Add new technologies
        for tech_data in project_data.technologies:
            db_tech = ProjectTechnologyModel(
                project_id=project_id,
                technology=tech_data.technology
            )
            db.add(db_tech)
    
    # Update achievements if provided
    if hasattr(project_data, 'achievements') and project_data.achievements is not None:
        # Delete existing achievements
        db.query(ProjectAchievementModel).filter(
            ProjectAchievementModel.project_id == project_id
        ).delete()
        
        # Add new achievements
        for achievement_data in project_data.achievements:
            db_achievement = ProjectAchievementModel(
                project_id=project_id,
                description=achievement_data.description
            )
            db.add(db_achievement)
    
    db.commit()
    db.refresh(project)
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project"""
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db.delete(project)
    db.commit()
    return None
