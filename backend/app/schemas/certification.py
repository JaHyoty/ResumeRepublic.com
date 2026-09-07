from pydantic import BaseModel, field_validator
from typing import Optional, Union
from datetime import date

class CertificationBase(BaseModel):
    name: str
    issuer: str
    issue_date: Optional[Union[date, str]] = None
    expiry_date: Optional[Union[date, str]] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None

    @field_validator("issue_date", "expiry_date", "credential_id", "credential_url", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

class CertificationCreate(CertificationBase):
    pass

class CertificationUpdate(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[Union[date, str]] = None
    expiry_date: Optional[Union[date, str]] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None

    @field_validator("issue_date", "expiry_date", "credential_id", "credential_url", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

class Certification(CertificationBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
