"""
Demo Authentication API routes (without database)
This is a simplified version for testing the frontend authentication flow
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import structlog

from app.core.config import settings

logger = structlog.get_logger()

router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# In-memory storage for demo
users_db = {}
tokens_db = {}

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    preferred_first_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    email: Optional[str] = None

class OAuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"

class User(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    preferred_first_name: Optional[str] = None
    is_verified: bool
    created_at: str

# Utility functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    # For demo purposes, we'll use a simple token
    import secrets
    token = secrets.token_urlsafe(32)
    tokens_db[token] = {
        "email": data.get("sub"),
        "exp": expire.isoformat()
    }
    return token

def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email from in-memory storage"""
    if email in users_db:
        user_data = users_db[email]
        return User(
            id=user_data["id"],
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            preferred_first_name=user_data.get("preferred_first_name"),
            is_verified=user_data["is_verified"],
            created_at=user_data["created_at"]
        )
    return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current authenticated user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token not in tokens_db:
        raise credentials_exception
    
    token_data = tokens_db[token]
    email = token_data["email"]
    
    user = get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user

# API Routes
@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    if user_data.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = len(users_db) + 1
    users_db[user_data.email] = {
        "id": user_id,
        "email": user_data.email,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "preferred_first_name": user_data.preferred_first_name,
        "password": user_data.password,  # In real app, this would be hashed
        "is_verified": False,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.email}, expires_delta=access_token_expires
    )
    
    logger.info("User registered", user_id=user_id, email=user_data.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with email and password"""
    email = form_data.username
    password = form_data.password
    
    if email not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_data = users_db[email]
    if user_data["password"] != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email}, expires_delta=access_token_expires
    )
    
    logger.info("User logged in", user_id=user_data["id"], email=email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/oauth/google", response_model=Token)
async def google_oauth(token: OAuthToken):
    """Login with Google OAuth (demo)"""
    # For demo purposes, create a mock user
    email = "demo@google.com"
    if email not in users_db:
        users_db[email] = {
            "id": len(users_db) + 1,
            "email": email,
            "first_name": "Google",
            "last_name": "User",
            "preferred_first_name": "Google",
            "is_verified": True,
            "created_at": datetime.utcnow().isoformat()
        }
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/oauth/github", response_model=Token)
async def github_oauth(token: OAuthToken):
    """Login with GitHub OAuth (demo)"""
    # For demo purposes, create a mock user
    email = "demo@github.com"
    if email not in users_db:
        users_db[email] = {
            "id": len(users_db) + 1,
            "email": email,
            "first_name": "GitHub",
            "last_name": "User",
            "preferred_first_name": "GitHub",
            "is_verified": True,
            "created_at": datetime.utcnow().isoformat()
        }
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "preferred_first_name": current_user.preferred_first_name,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
