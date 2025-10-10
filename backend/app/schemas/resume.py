"""
Resume generation schemas
"""

from pydantic import BaseModel
from typing import Optional


class PersonalInfo(BaseModel):
    name: str
    email: str
    phone: str
    location: Optional[str] = None
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


class ResumeDesignResponse(BaseModel):
    resume_generation_id: int
    status: str
    message: str


class KeywordAnalysisRequest(BaseModel):
    job_description: str


class KeywordAnalysisResponse(BaseModel):
    keywords: list[str]
