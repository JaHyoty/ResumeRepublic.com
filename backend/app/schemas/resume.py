"""
Resume generation schemas
"""

from pydantic import BaseModel
from typing import Optional


class PersonalInfo(BaseModel):
    name: str
    email: str
    phone: str
    location: str
    linkedin: Optional[str] = None
    website: Optional[str] = None
    summary: Optional[str] = None


class ResumeDesignRequest(BaseModel):
    personal_info: PersonalInfo
    job_title: str
    company: str
    job_description: str
    linked_application_id: Optional[int] = None
    locale: Optional[str] = "en-US"  # Default to US format
