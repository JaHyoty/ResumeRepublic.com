from pydantic import BaseModel
from typing import Optional
from datetime import date

class PublicationBase(BaseModel):
    title: str
    authors: Optional[str] = None
    publisher: Optional[str] = None
    publication_date: Optional[date] = None
    url: Optional[str] = None
    description: Optional[str] = None
    publication_type: Optional[str] = None  # e.g., "Journal", "Conference", "Blog", "Book"

class PublicationCreate(PublicationBase):
    pass

class PublicationUpdate(BaseModel):
    title: Optional[str] = None
    authors: Optional[str] = None
    publisher: Optional[str] = None
    publication_date: Optional[date] = None
    url: Optional[str] = None
    description: Optional[str] = None
    publication_type: Optional[str] = None

class Publication(PublicationBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
