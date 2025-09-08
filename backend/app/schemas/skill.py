from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SkillBase(BaseModel):
    name: str

class SkillCreate(SkillBase):
    pass

class SkillUpdate(BaseModel):
    name: Optional[str] = None

class Skill(SkillBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
