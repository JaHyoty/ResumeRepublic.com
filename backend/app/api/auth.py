"""
Real Authentication API routes with JWT and database
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import structlog

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import create_access_token, get_current_user
from app.core.password import verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse

logger = structlog.get_logger()

router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    db_user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        preferred_first_name=user_data.preferred_first_name,
        is_active=True,
        is_verified=False
    )
    
    # Set password hash
    db_user.set_password(user_data.password)
    
    # Save to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info("User registered", user_id=db_user.id, email=db_user.email)
    
    return db_user


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    
    # Find user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    # Verify user exists and password is correct
    if not user or not user.check_password(user_credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)}
    )
    
    logger.info("User logged in", user_id=user.id, email=user.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/login-form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login using OAuth2PasswordRequestForm (for Swagger UI)"""
    
    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Verify user exists and password is correct
    if not user or not user.check_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)}
    )
    
    logger.info("User logged in via form", user_id=user.id, email=user.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/logout")
async def logout():
    """Logout user (client should discard token)"""
    return {"message": "Successfully logged out"}


@router.get("/verify-token")
async def verify_token(current_user: User = Depends(get_current_user)):
    """Verify if token is valid"""
    return {"valid": True, "user_id": current_user.id}
