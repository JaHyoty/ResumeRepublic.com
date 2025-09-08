from pydantic import BaseModel
from typing import Optional
from datetime import date

class CertificationBase(BaseModel):
    name: str
    issuer: str
    issue_date: date
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None

class CertificationCreate(CertificationBase):
    pass

class CertificationUpdate(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None

class Certification(CertificationBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
