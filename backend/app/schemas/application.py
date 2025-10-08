"""
Pydantic schemas for applications
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ApplicationBase(BaseModel):
    """Base application schema"""
    online_assessment: bool = False
    interview: bool = False
    rejected: bool = False
    salary_range: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    application_metadata: Optional[Dict[str, Any]] = None
    job_posting_id: Optional[UUID] = None


class ApplicationUpdate(BaseModel):
    """Schema for updating an application"""
    online_assessment: Optional[bool] = None
    interview: Optional[bool] = None
    rejected: Optional[bool] = None
    salary_range: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    application_metadata: Optional[Dict[str, Any]] = None
    job_posting_id: Optional[UUID] = None


class ApplicationResponse(ApplicationBase):
    """Schema for application response"""
    id: int
    applied_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Job data from job_posting relationship
    job_title: Optional[str] = None
    company: Optional[str] = None
    job_description: Optional[str] = None

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
