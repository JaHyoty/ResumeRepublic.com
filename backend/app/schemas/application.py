"""
Pydantic schemas for applications
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ApplicationBase(BaseModel):
    """Base application schema"""
    job_title: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=100)
    job_description: Optional[str] = None
    online_assessment: bool = False
    interview: bool = False
    rejected: bool = False
    salary_range: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    application_metadata: Optional[Dict[str, Any]] = None


class ApplicationCreate(ApplicationBase):
    """Schema for creating a new application"""
    pass


class ApplicationUpdate(BaseModel):
    """Schema for updating an application"""
    job_title: Optional[str] = Field(None, min_length=1, max_length=255)
    company: Optional[str] = Field(None, min_length=1, max_length=100)
    job_description: Optional[str] = None
    online_assessment: Optional[bool] = None
    interview: Optional[bool] = None
    rejected: Optional[bool] = None
    salary_range: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    application_metadata: Optional[Dict[str, Any]] = None


class ApplicationResponse(ApplicationBase):
    """Schema for application response"""
    id: int
    user_id: int
    applied_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApplicationStats(BaseModel):
    """Schema for application statistics"""
    total_applications: int
    online_assessments: int
    interviews: int
    rejected: int
    online_assessment_rate: float
    interview_rate: float
    rejection_rate: float
