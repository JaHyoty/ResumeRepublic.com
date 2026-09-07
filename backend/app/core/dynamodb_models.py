"""
DynamoDB-based models for the serverless architecture.
These replace SQLAlchemy models with simple dict-based representations
and helper functions for DynamoDB key construction.

Each entity type has:
  - A dict builder that creates a DynamoDB item from parameters
  - A from_item() function that extracts the entity data from a DynamoDB item
  - Constants for SK prefixes
"""

from datetime import datetime, date, timezone
from typing import Any, Dict, List, Optional
import uuid


# ---------------------------------------------------------------------------
# SK prefix constants
# ---------------------------------------------------------------------------
SK_PROFILE = "PROFILE"
SK_EXP = "EXP#"
SK_EXPTITLE = "EXPTITLE#"
SK_SKILL = "SKILL#"
SK_EDU = "EDU#"
SK_CERT = "CERT#"
SK_PUB = "PUB#"
SK_PROJECT = "PROJECT#"
SK_WEBSITE = "WEBSITE#"
SK_APP = "APP#"
SK_RESUME = "RESUME#"
SK_JOBPOST = "JOBPOST"
SK_ATTEMPT = "ATTEMPT#"
SK_GENSTATUS = "GENSTATUS#"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

def build_user_item(
    user_id: int,
    email: str,
    first_name: str,
    last_name: str,
    preferred_first_name: Optional[str] = None,
    phone: Optional[str] = None,
    location: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    website_url: Optional[str] = None,
    professional_summary: Optional[str] = None,
    password_hash: Optional[str] = None,
    is_active: bool = True,
    is_verified: bool = False,
    terms_accepted_at: Optional[str] = None,
    privacy_policy_accepted_at: Optional[str] = None,
    created_at: Optional[str] = None,
    updated_at: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "PK": f"USER#{user_id}",
        "SK": SK_PROFILE,
        "GSI1PK": f"EMAIL#{email}",
        "GSI1SK": "USER",
        "entity_type": "user",
        "id": user_id,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "preferred_first_name": preferred_first_name,
        "phone": phone,
        "location": location,
        "linkedin_url": linkedin_url,
        "website_url": website_url,
        "professional_summary": professional_summary,
        "password_hash": password_hash,
        "is_active": is_active,
        "is_verified": is_verified,
        "terms_accepted_at": terms_accepted_at,
        "privacy_policy_accepted_at": privacy_policy_accepted_at,
        "created_at": created_at or _now_iso(),
        "updated_at": updated_at,
    }


class UserItem:
    """Wrapper around a DynamoDB user item dict for attribute access."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            return super().__getattribute__(name)
        return self._data.get(name)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self._data.items()
                if k not in ("PK", "SK", "GSI1PK", "GSI1SK", "entity_type")}

    def check_password(self, password: str) -> bool:
        from app.core.password import verify_password
        if not self._data.get("password_hash"):
            return False
        return verify_password(password, self._data["password_hash"])

    def set_password(self, password: str) -> None:
        from app.core.password import get_password_hash
        self._data["password_hash"] = get_password_hash(password)


# ---------------------------------------------------------------------------
# Experience
# ---------------------------------------------------------------------------

def build_experience_item(
    user_id: int,
    experience_id: int,
    company: str,
    start_date: Any,
    location: Optional[str] = None,
    end_date: Any = None,
    description: Optional[str] = None,
    is_current: bool = False,
    created_at: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "PK": f"USER#{user_id}",
        "SK": f"{SK_EXP}{experience_id}",
        "entity_type": "experience",
        "id": experience_id,
        "user_id": user_id,
        "company": company,
        "location": location,
        "start_date": str(start_date) if start_date else None,
        "end_date": str(end_date) if end_date else None,
        "description": description,
        "is_current": is_current,
        "created_at": created_at or _now_iso(),
    }


def build_experience_title_item(
    user_id: int,
    experience_id: int,
    title_id: int,
    title: str,
    is_primary: bool = False,
) -> Dict[str, Any]:
    return {
        "PK": f"USER#{user_id}",
        "SK": f"{SK_EXPTITLE}{experience_id}#{title_id}",
        "entity_type": "experience_title",
        "id": title_id,
        "experience_id": experience_id,
        "user_id": user_id,
        "title": title,
        "is_primary": is_primary,
    }


# ---------------------------------------------------------------------------
# Skill
# ---------------------------------------------------------------------------

def build_skill_item(
    user_id: int,
    skill_id: int,
    name: str,
) -> Dict[str, Any]:
    return {
        "PK": f"USER#{user_id}",
        "SK": f"{SK_SKILL}{skill_id}",
        "entity_type": "skill",
        "id": skill_id,
        "user_id": user_id,
        "name": name,
    }


# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------

def build_education_item(
    user_id: int,
    education_id: int,
    institution: str,
    degree: str,
    field_of_study: str,
    start_date: Any,
    end_date: Any,
    gpa: Optional[str] = None,
    coursework: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "PK": f"USER#{user_id}",
        "SK": f"{SK_EDU}{education_id}",
        "entity_type": "education",
        "id": education_id,
        "user_id": user_id,
        "institution": institution,
        "degree": degree,
        "field_of_study": field_of_study,
        "start_date": str(start_date) if start_date else None,
        "end_date": str(end_date) if end_date else None,
        "gpa": gpa,
        "coursework": coursework,
    }


# ---------------------------------------------------------------------------
# Certification
# ---------------------------------------------------------------------------

def build_certification_item(
    user_id: int,
    cert_id: int,
    name: str,
    issuer: str,
    issue_date: Any = None,
    expiry_date: Any = None,
    credential_id: Optional[str] = None,
    credential_url: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "PK": f"USER#{user_id}",
        "SK": f"{SK_CERT}{cert_id}",
        "entity_type": "certification",
        "id": cert_id,
        "user_id": user_id,
        "name": name,
        "issuer": issuer,
        "issue_date": str(issue_date) if issue_date else None,
        "expiry_date": str(expiry_date) if expiry_date else None,
        "credential_id": credential_id,
        "credential_url": credential_url,
    }


# ---------------------------------------------------------------------------
# Publication
# ---------------------------------------------------------------------------

def build_publication_item(
    user_id: int,
    pub_id: int,
    title: str,
    authors: Optional[str] = None,
    publisher: Optional[str] = None,
    publication_date: Any = None,
    url: Optional[str] = None,
    description: Optional[str] = None,
    publication_type: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "PK": f"USER#{user_id}",
        "SK": f"{SK_PUB}{pub_id}",
        "entity_type": "publication",
        "id": pub_id,
        "user_id": user_id,
        "title": title,
        "authors": authors,
        "publisher": publisher,
        "publication_date": str(publication_date) if publication_date else None,
        "url": url,
        "description": description,
        "publication_type": publication_type,
    }


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

def build_project_item(
    user_id: int,
    project_id: int,
    name: str,
    description: Optional[str] = None,
    role: Optional[str] = None,
    start_date: Any = None,
    end_date: Any = None,
    url: Optional[str] = None,
    is_current: bool = False,
    technologies_used: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "PK": f"USER#{user_id}",
        "SK": f"{SK_PROJECT}{project_id}",
        "entity_type": "project",
        "id": project_id,
        "user_id": user_id,
        "name": name,
        "description": description,
        "role": role,
        "start_date": str(start_date) if start_date else None,
        "end_date": str(end_date) if end_date else None,
        "url": url,
        "is_current": is_current,
        "technologies_used": technologies_used,
    }


# ---------------------------------------------------------------------------
# Website
# ---------------------------------------------------------------------------

def build_website_item(
    user_id: int,
    website_id: int,
    site_name: str,
    url: str,
    created_at: Optional[str] = None,
    updated_at: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "PK": f"USER#{user_id}",
        "SK": f"{SK_WEBSITE}{website_id}",
        "entity_type": "website",
        "id": website_id,
        "user_id": user_id,
        "site_name": site_name,
        "url": url,
        "created_at": created_at or _now_iso(),
        "updated_at": updated_at,
    }


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

def build_application_item(
    user_id: int,
    app_id: int,
    applied_date: Optional[str] = None,
    online_assessment: bool = False,
    interview: bool = False,
    rejected: bool = False,
    salary_range: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    experience_level: Optional[str] = None,
    application_metadata: Optional[Dict] = None,
    job_posting_id: Optional[str] = None,
    created_at: Optional[str] = None,
    updated_at: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "PK": f"USER#{user_id}",
        "SK": f"{SK_APP}{app_id}",
        "entity_type": "application",
        "id": app_id,
        "user_id": user_id,
        "applied_date": applied_date or _now_iso(),
        "online_assessment": online_assessment,
        "interview": interview,
        "rejected": rejected,
        "salary_range": salary_range,
        "location": location,
        "job_type": job_type,
        "experience_level": experience_level,
        "application_metadata": application_metadata,
        "job_posting_id": job_posting_id,
        "created_at": created_at or _now_iso(),
        "updated_at": updated_at,
    }


# ---------------------------------------------------------------------------
# ResumeVersion
# ---------------------------------------------------------------------------

def build_resume_version_item(
    user_id: int,
    resume_id: int,
    application_id: int,
    title: str,
    template_used: Optional[str] = None,
    pdf_url: Optional[str] = None,
    s3_key: Optional[str] = None,
    latex_s3_key: Optional[str] = None,
    resume_metadata: Optional[Dict] = None,
    created_at: Optional[str] = None,
    updated_at: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "PK": f"USER#{user_id}",
        "SK": f"{SK_RESUME}{application_id}#{resume_id}",
        "entity_type": "resume_version",
        "id": resume_id,
        "user_id": user_id,
        "application_id": application_id,
        "title": title,
        "template_used": template_used,
        "pdf_url": pdf_url,
        "s3_key": s3_key,
        "latex_s3_key": latex_s3_key,
        "resume_metadata": resume_metadata,
        "created_at": created_at or _now_iso(),
        "updated_at": updated_at,
    }


# ---------------------------------------------------------------------------
# JobPosting
# ---------------------------------------------------------------------------

def build_job_posting_item(
    job_posting_id: str,
    url: Optional[str] = None,
    domain: Optional[str] = None,
    created_by_user_id: Optional[int] = None,
    title: Optional[str] = None,
    company: Optional[str] = None,
    description: Optional[str] = None,
    status: str = "pending",
    provenance: Optional[Dict] = None,
    raw_snapshot: Optional[Dict] = None,
    created_at: Optional[str] = None,
    updated_at: Optional[str] = None,
) -> Dict[str, Any]:
    item: Dict[str, Any] = {
        "PK": f"JOBPOST#{job_posting_id}",
        "SK": SK_JOBPOST,
        "entity_type": "job_posting",
        "id": job_posting_id,
        "status": status,
        "created_at": created_at or _now_iso(),
        "updated_at": updated_at,
    }
    # Use GSI1 for URL-based lookups
    if url:
        item["GSI1PK"] = f"JOBURL#{url}"
        item["GSI1SK"] = "JOBPOST"
        item["url"] = url
    if domain:
        item["domain"] = domain
    if created_by_user_id is not None:
        item["created_by_user_id"] = created_by_user_id
    if title:
        item["title"] = title
    if company:
        item["company"] = company
    if description:
        item["description"] = description
    if provenance:
        item["provenance"] = provenance
    if raw_snapshot:
        item["raw_snapshot"] = raw_snapshot
    return item


def build_fetch_attempt_item(
    job_posting_id: str,
    attempt_id: str,
    method: str,
    response_code: Optional[int] = None,
    duration_ms: Optional[int] = None,
    success: bool = False,
    error_message: Optional[str] = None,
    note: Optional[str] = None,
    created_at: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "PK": f"JOBPOST#{job_posting_id}",
        "SK": f"{SK_ATTEMPT}{attempt_id}",
        "entity_type": "fetch_attempt",
        "id": attempt_id,
        "job_posting_id": job_posting_id,
        "method": method,
        "response_code": response_code,
        "duration_ms": duration_ms,
        "success": success,
        "error_message": error_message,
        "note": note,
        "created_at": created_at or _now_iso(),
    }


# ---------------------------------------------------------------------------
# Resume Generation Status (replaces SSE)
# ---------------------------------------------------------------------------

def build_gen_status_item(
    user_id: int,
    resume_id: int,
    status: str,
    message: Optional[str] = None,
    data: Optional[Dict] = None,
    updated_at: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "PK": f"USER#{user_id}",
        "SK": f"{SK_GENSTATUS}{resume_id}",
        "entity_type": "gen_status",
        "resume_id": resume_id,
        "user_id": user_id,
        "status": status,
        "message": message,
        "data": data,
        "updated_at": updated_at or _now_iso(),
    }


# ---------------------------------------------------------------------------
# Generic item wrapper for attribute-style access
# ---------------------------------------------------------------------------

class DynamoItem:
    """Generic wrapper that provides attribute-style access to a DynamoDB item dict."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            return super().__getattribute__(name)
        return self._data.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self._data.items()
                if k not in ("PK", "SK", "GSI1PK", "GSI1SK", "entity_type")}

    def __repr__(self) -> str:
        etype = self._data.get("entity_type", "unknown")
        eid = self._data.get("id", "?")
        return f"<DynamoItem({etype}, id={eid})>"
