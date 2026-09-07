"""
Project schemas for API serialization
"""

from pydantic import BaseModel, field_validator
from typing import Optional, Union
from datetime import date


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    role: Optional[str] = None  # New field for role
    start_date: Optional[Union[date, str]] = None  # Made optional
    end_date: Optional[Union[date, str]] = None
    url: Optional[str] = None
    is_current: bool = False
    technologies_used: Optional[str] = None  # Comma-separated text field

    @field_validator("start_date", "end_date", "url", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[Union[date, str]] = None
    end_date: Optional[Union[date, str]] = None
    url: Optional[str] = None
    is_current: Optional[bool] = None
    technologies_used: Optional[str] = None

    @field_validator("start_date", "end_date", "url", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v


class Project(ProjectBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True