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
from app.models.experience import Experience as ExperienceModel, ExperienceTitle as ExperienceTitleModel, Achievement as AchievementModel
from app.models.skill import Skill as SkillModel
from app.models.certification import Certification as CertificationModel
from app.models.publication import Publication as PublicationModel
from app.schemas.experience import Experience, ExperienceCreate, ExperienceUpdate
from app.schemas.skill import Skill, SkillCreate, SkillUpdate
from app.schemas.certification import Certification, CertificationCreate, CertificationUpdate
from app.schemas.publication import Publication, PublicationCreate, PublicationUpdate

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
    
    # Add achievements
    for achievement_data in experience_data.achievements:
        db_achievement = AchievementModel(
            experience_id=db_experience.id,
            description=achievement_data.description
        )
        db.add(db_achievement)
    
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
    
    # Update fields if provided
    update_data = experience_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(experience, field, value)
    
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


# TODO: Implement other ESC routes
# - GET /tools
# - POST /tools
# - GET /publications
# - POST /publications
# - PUT /publications/{id}
# - DELETE /publications/{id}
# - GET /certifications
# - POST /certifications
# - PUT /certifications/{id}
# - DELETE /certifications/{id}
