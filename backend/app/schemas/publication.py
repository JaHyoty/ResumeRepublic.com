from pydantic import BaseModel, field_validator
from typing import Optional, Union
from datetime import date

class PublicationBase(BaseModel):
    title: str
    authors: Optional[str] = None
    publisher: Optional[str] = None
    publication_date: Optional[Union[date, str]] = None
    url: Optional[str] = None
    description: Optional[str] = None
    publication_type: Optional[str] = None  # e.g., "Journal", "Conference", "Blog", "Book"

    @field_validator("publication_date", "url", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

class PublicationCreate(PublicationBase):
    pass

class PublicationUpdate(BaseModel):
    title: Optional[str] = None
    authors: Optional[str] = None
    publisher: Optional[str] = None
    publication_date: Optional[Union[date, str]] = None
    url: Optional[str] = None
    description: Optional[str] = None
    publication_type: Optional[str] = None

    @field_validator("publication_date", "url", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

class Publication(PublicationBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
