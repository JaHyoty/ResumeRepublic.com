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
from app.schemas.experience import Experience, ExperienceCreate, ExperienceUpdate

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


# TODO: Implement other ESC routes
# - GET /skills
# - POST /skills
# - PUT /skills/{id}
# - DELETE /skills/{id}
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
