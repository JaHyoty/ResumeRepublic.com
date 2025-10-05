"""
User schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# Original user schemas
class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    preferred_first_name: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_first_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    professional_summary: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class GoogleOAuthRequest(BaseModel):
    """Schema for Google OAuth login"""
    id_token: str


class GitHubOAuthRequest(BaseModel):
    """Schema for GitHub OAuth login"""
    code: str


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str
    expires_in: int
    needs_agreement: Optional[bool] = False


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    preferred_first_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    professional_summary: Optional[str] = None
    is_active: bool
    is_verified: bool
    terms_accepted_at: Optional[datetime] = None
    privacy_policy_accepted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TermsAgreementRequest(BaseModel):
    """Schema for terms and privacy policy agreement"""
    terms_accepted: bool
    privacy_policy_accepted: bool


# Profile-specific schemas (aliases for backward compatibility)
UserProfile = UserResponse
UserProfileUpdate = UserUpdate
UserProfileBase = UserCreate