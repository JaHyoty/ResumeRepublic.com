"""
Website schemas
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class WebsiteBase(BaseModel):
    """Base website schema"""
    site_name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl = Field(..., max_length=500)

class WebsiteCreate(WebsiteBase):
    """Schema for creating website"""
    pass

class WebsiteUpdate(BaseModel):
    """Schema for updating website"""
    site_name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[HttpUrl] = Field(None, max_length=500)

class Website(WebsiteBase):
    """Schema for website response"""
    id: int

    class Config:
        from_attributes = True
