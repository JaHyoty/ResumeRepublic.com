"""
Project-related Pydantic schemas
"""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel


class ProjectTechnologyBase(BaseModel):
    technology: str


class ProjectTechnologyCreate(ProjectTechnologyBase):
    pass


class ProjectTechnology(ProjectTechnologyBase):
    id: int
    project_id: int

    class Config:
        from_attributes = True


class ProjectAchievementBase(BaseModel):
    description: str


class ProjectAchievementCreate(ProjectAchievementBase):
    pass


class ProjectAchievement(ProjectAchievementBase):
    id: int
    project_id: int

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    url: Optional[str] = None
    is_current: bool = False


class ProjectCreate(ProjectBase):
    technologies: List[ProjectTechnologyCreate] = []
    achievements: List[ProjectAchievementCreate] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    url: Optional[str] = None
    is_current: Optional[bool] = None
    technologies: Optional[List[ProjectTechnologyCreate]] = None
    achievements: Optional[List[ProjectAchievementCreate]] = None


class Project(ProjectBase):
    id: int
    user_id: int
    technologies: List[ProjectTechnology] = []
    achievements: List[ProjectAchievement] = []

    class Config:
        from_attributes = True
