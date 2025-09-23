"""
Experience-related Pydantic schemas
"""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel


class ExperienceTitleBase(BaseModel):
    title: str
    is_primary: bool = False


class ExperienceTitleCreate(ExperienceTitleBase):
    pass


class ExperienceTitle(ExperienceTitleBase):
    id: int
    experience_id: int

    class Config:
        from_attributes = True


class ExperienceBase(BaseModel):
    company: str
    location: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None
    is_current: bool = False


class ExperienceCreate(ExperienceBase):
    titles: List[ExperienceTitleCreate] = []


class ExperienceUpdate(BaseModel):
    company: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    is_current: Optional[bool] = None
    titles: Optional[List[ExperienceTitleCreate]] = None


class Experience(ExperienceBase):
    id: int
    user_id: int
    titles: List[ExperienceTitle] = []

    class Config:
        from_attributes = True
