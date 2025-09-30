"""
Project schemas for API serialization
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    url: Optional[str] = None
    is_current: bool = False
    technologies_used: Optional[str] = None  # Comma-separated text field


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    url: Optional[str] = None
    is_current: Optional[bool] = None
    technologies_used: Optional[str] = None


class Project(ProjectBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True