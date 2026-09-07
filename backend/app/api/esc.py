"""
Experience and Skills Catalog API routes — DynamoDB version
"""

from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.core.dynamodb import DynamoDBClient, get_db
from app.core.auth import get_current_user
from app.core.dynamodb_models import (
    UserItem, DynamoItem,
    build_experience_item, build_experience_title_item,
    build_skill_item, build_certification_item,
    build_publication_item, build_education_item,
    build_website_item, build_project_item,
    SK_EXP, SK_EXPTITLE, SK_SKILL, SK_CERT, SK_PUB, SK_EDU, SK_WEBSITE, SK_PROJECT,
)
from app.schemas.experience import Experience, ExperienceCreate, ExperienceUpdate
from app.schemas.skill import Skill, SkillCreate, SkillUpdate
from app.schemas.certification import Certification, CertificationCreate, CertificationUpdate
from app.schemas.publication import Publication, PublicationCreate, PublicationUpdate
from app.schemas.education import Education, EducationCreate, EducationUpdate
from app.schemas.website import Website, WebsiteCreate, WebsiteUpdate
from app.schemas.project import Project, ProjectCreate, ProjectUpdate

logger = structlog.get_logger()
router = APIRouter()


def _user_pk(user: UserItem) -> str:
    return f"USER#{user.id}"


def _attach_titles(db: DynamoDBClient, user_pk: str, experience: dict) -> dict:
    """Attach titles list to an experience dict."""
    exp_id = experience["id"]
    titles = db.query(user_pk, sk_prefix=f"{SK_EXPTITLE}{exp_id}#")
    experience["titles"] = titles
    return experience


# =====================================================================
# Experiences
# =====================================================================

@router.get("/experiences", response_model=List[Experience])
def get_user_experiences(
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get all experiences for the current user"""
    pk = _user_pk(current_user)
    experiences = db.query(pk, sk_prefix=SK_EXP)
    # Filter out experience titles (they share the EXP prefix pattern but have EXPTITLE)
    experiences = [e for e in experiences if e.get("entity_type") == "experience"]

    # Attach titles
    for exp in experiences:
        _attach_titles(db, pk, exp)

    # Sort: current first, then by end_date desc, then start_date desc
    def sort_key(e):
        is_current = 0 if e.get("is_current") else 1
        end = e.get("end_date") or "9999-12-31"
        start = e.get("start_date") or "0000-01-01"
        return (is_current, end, start)

    experiences.sort(key=sort_key, reverse=False)
    # Reverse the date sorting (we want desc)
    experiences.sort(key=lambda e: (0 if e.get("is_current") else 1))

    return experiences


@router.post("/experiences", response_model=Experience, status_code=status.HTTP_201_CREATED)
def create_experience(
    experience_data: ExperienceCreate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Create a new work experience"""
    pk = _user_pk(current_user)
    exp_id = db.next_id("experience")

    exp_item = build_experience_item(
        user_id=current_user.id,
        experience_id=exp_id,
        company=experience_data.company,
        location=experience_data.location,
        start_date=experience_data.start_date,
        end_date=experience_data.end_date,
        description=experience_data.description,
        is_current=experience_data.is_current,
    )
    db.put_item(exp_item)

    # Create titles
    titles = []
    for title_data in experience_data.titles:
        title_id = db.next_id("experience_title")
        title_item = build_experience_title_item(
            user_id=current_user.id,
            experience_id=exp_id,
            title_id=title_id,
            title=title_data.title,
            is_primary=title_data.is_primary,
        )
        db.put_item(title_item)
        titles.append(title_item)

    exp_item["titles"] = titles
    return exp_item


@router.get("/experiences/{experience_id}", response_model=Experience)
def get_experience(
    experience_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get a specific experience by ID"""
    pk = _user_pk(current_user)
    exp = db.get_item(pk, f"{SK_EXP}{experience_id}")
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experience not found")
    _attach_titles(db, pk, exp)
    return exp


@router.put("/experiences/{experience_id}", response_model=Experience)
def update_experience(
    experience_id: int,
    experience_data: ExperienceUpdate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Update an existing experience"""
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_EXP}{experience_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experience not found")

    update_data = experience_data.model_dump(exclude_unset=True, exclude={"titles"})
    # Convert date objects to strings
    for key in ("start_date", "end_date"):
        if key in update_data and update_data[key] is not None:
            update_data[key] = str(update_data[key])

    if update_data:
        db.update_item(pk, f"{SK_EXP}{experience_id}", update_data)

    # Update titles if provided
    if hasattr(experience_data, "titles") and experience_data.titles is not None:
        # Delete existing titles
        old_titles = db.query(pk, sk_prefix=f"{SK_EXPTITLE}{experience_id}#")
        if old_titles:
            db.batch_delete([{"PK": t["PK"], "SK": t["SK"]} for t in old_titles])

        # Create new titles
        for title_data in experience_data.titles:
            title_id = db.next_id("experience_title")
            title_item = build_experience_title_item(
                user_id=current_user.id,
                experience_id=experience_id,
                title_id=title_id,
                title=title_data.title,
                is_primary=title_data.is_primary,
            )
            db.put_item(title_item)

    # Return updated experience
    result = db.get_item(pk, f"{SK_EXP}{experience_id}")
    _attach_titles(db, pk, result)
    return result


@router.delete("/experiences/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experience(
    experience_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Delete an experience"""
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_EXP}{experience_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experience not found")

    # Delete titles first
    titles = db.query(pk, sk_prefix=f"{SK_EXPTITLE}{experience_id}#")
    if titles:
        db.batch_delete([{"PK": t["PK"], "SK": t["SK"]} for t in titles])

    db.delete_item(pk, f"{SK_EXP}{experience_id}")
    return None


# =====================================================================
# Skills
# =====================================================================

@router.get("/skills", response_model=List[Skill])
def get_user_skills(
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get all skills for the current user"""
    skills = db.query(_user_pk(current_user), sk_prefix=SK_SKILL)
    skills.sort(key=lambda s: s.get("name", "").lower())
    return skills


@router.post("/skills", response_model=Skill)
def create_skill(
    skill: SkillCreate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Create a new skill"""
    skill_id = db.next_id("skill")
    item = build_skill_item(user_id=current_user.id, skill_id=skill_id, name=skill.name)
    db.put_item(item)
    return item


@router.post("/skills/bulk", response_model=List[Skill])
def create_skills_bulk(
    skill_names: List[str],
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Create multiple skills at once from a list of skill names"""
    if not skill_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No skill names provided"
        )

    # Get existing skill names for the user to avoid duplicates
    existing_skills = db.query(_user_pk(current_user), sk_prefix=SK_SKILL)
    existing_skill_names = {s.get("name", "").lower() for s in existing_skills}

    created = []
    for skill_name in skill_names:
        name_clean = skill_name.strip()
        if name_clean and name_clean.lower() not in existing_skill_names:
            skill_id = db.next_id("skill")
            item = build_skill_item(user_id=current_user.id, skill_id=skill_id, name=name_clean)
            db.put_item(item)
            created.append(item)
            existing_skill_names.add(name_clean.lower())

    return created


@router.get("/skills/{skill_id}", response_model=Skill)
def get_skill(
    skill_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Get a specific skill by ID"""
    item = db.get_item(_user_pk(current_user), f"{SK_SKILL}{skill_id}")
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return item


@router.put("/skills/{skill_id}", response_model=Skill)
def update_skill(
    skill_id: int,
    skill_update: SkillUpdate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Update a skill"""
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_SKILL}{skill_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")

    update_data = skill_update.model_dump(exclude_unset=True)
    if update_data:
        return db.update_item(pk, f"{SK_SKILL}{skill_id}", update_data)
    return existing


@router.delete("/skills/{skill_id}")
def delete_skill(
    skill_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    """Delete a skill"""
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_SKILL}{skill_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    db.delete_item(pk, f"{SK_SKILL}{skill_id}")
    return {"message": "Skill deleted successfully"}


# =====================================================================
# Certifications
# =====================================================================

@router.get("/certifications", response_model=List[Certification])
def get_user_certifications(
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    certs = db.query(_user_pk(current_user), sk_prefix=SK_CERT)
    certs.sort(key=lambda c: c.get("issue_date") or "", reverse=True)
    return certs


@router.post("/certifications", response_model=Certification)
def create_certification(
    cert_data: CertificationCreate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    cert_id = db.next_id("certification")
    item = build_certification_item(
        user_id=current_user.id, cert_id=cert_id, **cert_data.model_dump()
    )
    db.put_item(item)
    return item


@router.put("/certifications/{certification_id}", response_model=Certification)
def update_certification(
    certification_id: int,
    cert_data: CertificationUpdate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_CERT}{certification_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found")
    update_data = cert_data.model_dump(exclude_unset=True, exclude_none=False)
    for key in ("issue_date", "expiry_date"):
        if key in update_data and update_data[key] is not None:
            update_data[key] = str(update_data[key])
    if update_data:
        return db.update_item(pk, f"{SK_CERT}{certification_id}", update_data)
    return existing


@router.delete("/certifications/{certification_id}")
def delete_certification(
    certification_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_CERT}{certification_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certification not found")
    db.delete_item(pk, f"{SK_CERT}{certification_id}")
    return {"message": "Certification deleted successfully"}


# =====================================================================
# Publications
# =====================================================================

@router.get("/publications", response_model=List[Publication])
def get_user_publications(
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    pubs = db.query(_user_pk(current_user), sk_prefix=SK_PUB)
    pubs.sort(key=lambda p: p.get("publication_date") or "", reverse=True)
    return pubs


@router.post("/publications", response_model=Publication)
def create_publication(
    pub_data: PublicationCreate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    pub_id = db.next_id("publication")
    item = build_publication_item(user_id=current_user.id, pub_id=pub_id, **pub_data.model_dump())
    db.put_item(item)
    return item


@router.put("/publications/{publication_id}", response_model=Publication)
def update_publication(
    publication_id: int,
    pub_data: PublicationUpdate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_PUB}{publication_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found")
    update_data = pub_data.model_dump(exclude_unset=True, exclude_none=False)
    if "publication_date" in update_data and update_data["publication_date"] is not None:
        update_data["publication_date"] = str(update_data["publication_date"])
    if update_data:
        return db.update_item(pk, f"{SK_PUB}{publication_id}", update_data)
    return existing


@router.delete("/publications/{publication_id}")
def delete_publication(
    publication_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_PUB}{publication_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found")
    db.delete_item(pk, f"{SK_PUB}{publication_id}")
    return {"message": "Publication deleted successfully"}


# =====================================================================
# Education
# =====================================================================

@router.get("/education", response_model=List[Education])
def get_user_education(
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    edu = db.query(_user_pk(current_user), sk_prefix=SK_EDU)
    edu.sort(key=lambda e: e.get("start_date") or "", reverse=True)
    return edu


@router.post("/education", response_model=Education)
def create_education(
    education_data: EducationCreate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    edu_id = db.next_id("education")
    item = build_education_item(user_id=current_user.id, education_id=edu_id, **education_data.model_dump())
    db.put_item(item)
    return item


@router.put("/education/{education_id}", response_model=Education)
def update_education(
    education_id: int,
    education_data: EducationUpdate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_EDU}{education_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Education entry not found")
    update_data = education_data.model_dump(exclude_unset=True, exclude_none=False)
    for key in ("start_date", "end_date"):
        if key in update_data and update_data[key] is not None:
            update_data[key] = str(update_data[key])
    if update_data:
        return db.update_item(pk, f"{SK_EDU}{education_id}", update_data)
    return existing


@router.delete("/education/{education_id}")
def delete_education(
    education_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_EDU}{education_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Education entry not found")
    db.delete_item(pk, f"{SK_EDU}{education_id}")
    return {"message": "Education entry deleted successfully"}


# =====================================================================
# Websites
# =====================================================================

@router.get("/websites", response_model=List[Website])
def get_user_websites(
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    sites = db.query(_user_pk(current_user), sk_prefix=SK_WEBSITE)
    sites.sort(key=lambda s: s.get("created_at") or "", reverse=True)
    return sites


@router.post("/websites", response_model=Website)
def create_website(
    website_data: WebsiteCreate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    site_id = db.next_id("website")
    item = build_website_item(
        user_id=current_user.id,
        website_id=site_id,
        site_name=website_data.site_name,
        url=str(website_data.url),
    )
    db.put_item(item)
    return item


@router.put("/websites/{website_id}", response_model=Website)
def update_website(
    website_id: int,
    website_data: WebsiteUpdate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_WEBSITE}{website_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
    updates = {}
    if website_data.site_name is not None:
        updates["site_name"] = website_data.site_name
    if website_data.url is not None:
        updates["url"] = str(website_data.url)
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        return db.update_item(pk, f"{SK_WEBSITE}{website_id}", updates)
    return existing


@router.delete("/websites/{website_id}")
def delete_website(
    website_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_WEBSITE}{website_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
    db.delete_item(pk, f"{SK_WEBSITE}{website_id}")
    return {"message": "Website deleted successfully"}


# =====================================================================
# Projects
# =====================================================================

@router.get("/projects", response_model=List[Project])
def get_user_projects(
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    projects = db.query(_user_pk(current_user), sk_prefix=SK_PROJECT)
    # Sort: current first, then by end_date desc
    projects.sort(
        key=lambda p: (
            0 if p.get("is_current") else 1,
            p.get("end_date") or "9999-12-31",
            p.get("start_date") or "0000-01-01",
        ),
        reverse=False,
    )
    return projects


@router.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    proj_id = db.next_id("project")
    item = build_project_item(user_id=current_user.id, project_id=proj_id, **project_data.model_dump())
    db.put_item(item)
    return item


@router.get("/projects/{project_id}", response_model=Project)
def get_project(
    project_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    item = db.get_item(_user_pk(current_user), f"{SK_PROJECT}{project_id}")
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return item


@router.put("/projects/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_PROJECT}{project_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    update_data = project_data.model_dump(exclude_unset=True)
    for key in ("start_date", "end_date"):
        if key in update_data and update_data[key] is not None:
            update_data[key] = str(update_data[key])
    if update_data:
        return db.update_item(pk, f"{SK_PROJECT}{project_id}", update_data)
    return existing


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: UserItem = Depends(get_current_user),
    db: DynamoDBClient = Depends(get_db),
):
    pk = _user_pk(current_user)
    existing = db.get_item(pk, f"{SK_PROJECT}{project_id}")
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    db.delete_item(pk, f"{SK_PROJECT}{project_id}")
    return None
