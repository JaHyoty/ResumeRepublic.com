"""
Pydantic schemas for job posting parsing
"""

from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class JobPostingFetchRequest(BaseModel):
    """Request schema for fetching job posting data from URL"""
    url: HttpUrl = Field(..., description="URL of the job posting to parse")
    source: str = Field(default="web-ui", pattern=r'^(web-ui|api)$', description="Source of the request")

    @validator('url')
    def validate_url(cls, v):
        """Ensure URL is from a supported domain"""
        url_str = str(v)
        if not url_str.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class JobPostingFetchResponse(BaseModel):
    """Response schema for job posting fetch initiation"""
    job_posting_id: UUID = Field(..., description="Unique identifier for the parsing job")
    status: str = Field(..., description="Current status of the parsing job")
    message: str = Field(default="Job posting parsing initiated", description="Status message")


class JobPostingCreateRequest(BaseModel):
    """Request schema for manually creating job posting data"""
    title: str = Field(..., min_length=1, max_length=500, description="Job title")
    company: str = Field(..., min_length=1, max_length=255, description="Company name")
    description: str = Field(..., min_length=10, description="Job description")
    url: Optional[HttpUrl] = Field(None, description="Optional URL for the job posting")


class ProvenanceInfo(BaseModel):
    """Schema for extraction provenance information"""
    method: str = Field(..., description="Extraction method used")
    extractor: Optional[str] = Field(None, description="Specific extractor used")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")
    excerpt: Optional[str] = Field(None, description="Sample of extracted text")
    timestamp: datetime = Field(..., description="When extraction occurred")


class JobPostingResponse(BaseModel):
    """Response schema for job posting data"""
    id: UUID = Field(..., description="Unique identifier")
    url: Optional[str] = Field(None, description="Original URL")
    domain: Optional[str] = Field(None, description="Domain of the URL")
    created_by_user_id: Optional[int] = Field(None, description="User who created this job posting")
    title: Optional[str] = Field(None, description="Extracted job title")
    company: Optional[str] = Field(None, description="Extracted company name")
    description: Optional[str] = Field(None, description="Extracted job description")
    status: str = Field(..., description="Current parsing status")
    provenance: Optional[ProvenanceInfo] = Field(None, description="Extraction provenance")
    created_at: datetime = Field(..., description="When job posting was created")
    updated_at: datetime = Field(..., description="When job posting was last updated")

    class Config:
        from_attributes = True


class JobPostingListResponse(BaseModel):
    """Response schema for listing job postings"""
    job_postings: List[JobPostingResponse] = Field(..., description="List of job postings")
    total: int = Field(..., description="Total number of job postings")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of items per page")


class FetchAttemptResponse(BaseModel):
    """Response schema for fetch attempt data"""
    id: UUID = Field(..., description="Unique identifier")
    job_posting_id: UUID = Field(..., description="Associated job posting ID")
    method: str = Field(..., description="Extraction method attempted")
    response_code: Optional[int] = Field(None, description="HTTP response code")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")
    success: bool = Field(..., description="Whether attempt was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    note: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(..., description="When attempt was made")

    class Config:
        from_attributes = True
