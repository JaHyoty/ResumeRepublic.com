"""
Education schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class EducationBase(BaseModel):
    """Base education schema"""
    institution: str = Field(..., min_length=1, max_length=255)
    degree: str = Field(..., min_length=1, max_length=255)
    field_of_study: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: date  # Mandatory graduation date
    gpa: Optional[str] = Field(None, max_length=10)
    coursework: Optional[str] = None  # Renamed from description


class EducationCreate(EducationBase):
    """Schema for creating education"""
    pass


class EducationUpdate(BaseModel):
    """Schema for updating education"""
    institution: Optional[str] = Field(None, min_length=1, max_length=255)
    degree: Optional[str] = Field(None, min_length=1, max_length=255)
    field_of_study: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[str] = Field(None, max_length=10)
    coursework: Optional[str] = None


class Education(EducationBase):
    """Schema for education response"""
    id: int

    class Config:
        from_attributes = True
