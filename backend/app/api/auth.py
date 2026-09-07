"""
Real Authentication API routes with JWT cookies — DynamoDB version
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import structlog

from app.core.settings import settings
from app.core.dynamodb import DynamoDBClient, get_db
from app.core.auth import (
    create_access_token,
    get_current_user,
    set_auth_cookies,
    clear_auth_cookies,
    verify_token,
)
from app.core.limiter import limiter
from app.core.password import verify_password
from app.core.google_oauth import google_oauth_service
from app.core.dynamodb_models import UserItem, build_user_item
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse, GoogleOAuthRequest

logger = structlog.get_logger()

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


@router.post("/register", response_model=UserResponse)
@limiter.limit("3/minute")
async def register(request: Request, user_data: UserCreate, db: DynamoDBClient = Depends(get_db)):
    """Register a new user"""

    # Check if user already exists by email (GSI1 lookup)
    existing = db.query_gsi1(f"EMAIL#{user_data.email}", "USER")
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Generate new user ID
    user_id = db.next_id("user")

    # Build user item
    user_item = build_user_item(
        user_id=user_id,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        preferred_first_name=user_data.preferred_first_name,
        is_active=True,
        is_verified=False,
    )

    # Set password
    user = UserItem(user_item)
    user.set_password(user_data.password)
    user_item["password_hash"] = user.password_hash

    # Save to DynamoDB
    db.put_item(user_item)

    logger.info("User registered", user_id=user_id, email=user_data.email)

    return user.to_dict()


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    user_credentials: UserLogin,
    response: Response,
    db: DynamoDBClient = Depends(get_db),
):
    """Login user and set auth cookies"""

    # Find user by email
    results = db.query_gsi1(f"EMAIL#{user_credentials.email}", "USER")
    if not results:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserItem(results[0])

    if not user.check_password(user_credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    token_meta = set_auth_cookies(response, user.id)
    logger.info("User logged in", user_id=user.id, email=user.email)

    return {**token_meta, "message": "Login successful"}


@router.post("/login-form")
@limiter.limit("5/minute")
async def login_form(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: DynamoDBClient = Depends(get_db),
):
    """Login using OAuth2PasswordRequestForm (for Swagger UI)"""

    results = db.query_gsi1(f"EMAIL#{form_data.username}", "USER")
    if not results:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserItem(results[0])

    if not user.check_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    token_meta = set_auth_cookies(response, user.id)
    logger.info("User logged in via form", user_id=user.id, email=user.email)

    return {**token_meta, "message": "Login successful"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserItem = Depends(get_current_user)):
    """Get current user information"""
    return current_user.to_dict()


@router.post("/logout")
async def logout(response: Response):
    """Logout user - clears auth cookies"""
    clear_auth_cookies(response)
    return {"message": "Successfully logged out"}


@router.get("/verify-token")
async def verify_token_endpoint(current_user: UserItem = Depends(get_current_user)):
    """Verify if token is valid"""
    return {"valid": True, "user_id": current_user.id}


@router.post("/refresh")
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    response: Response,
    db: DynamoDBClient = Depends(get_db),
):
    """Refresh access token using refresh token cookie."""
    refresh_cookie = request.cookies.get("refresh_token")
    if not refresh_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    payload = verify_token(refresh_cookie, expected_type="refresh")
    if payload is None:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Verify the user still exists and is active
    user_data = db.get_item(f"USER#{user_id}", "PROFILE")
    if not user_data or not user_data.get("is_active", False):
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    user = UserItem(user_data)
    token_meta = set_auth_cookies(response, user.id)
    logger.info("Token refreshed", user_id=user.id)

    return {**token_meta, "message": "Token refreshed"}


@router.post("/google")
@limiter.limit("5/minute")
async def google_oauth_login(
    request: Request,
    oauth_data: GoogleOAuthRequest,
    response: Response,
    db: DynamoDBClient = Depends(get_db),
):
    """Login with Google OAuth"""

    google_user_info = await google_oauth_service.verify_id_token(oauth_data.id_token)
    if not google_user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    if not google_user_info.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google email not verified",
        )

    email = google_user_info["email"]

    # Check if user already exists by email
    existing = db.query_gsi1(f"EMAIL#{email}", "USER")

    if existing:
        user = UserItem(existing[0])
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive",
            )
        logger.info("Existing user logged in via Google OAuth", user_id=user.id, email=email)
    else:
        # Create new user
        user_id = db.next_id("user")
        user_item = build_user_item(
            user_id=user_id,
            email=email,
            first_name=google_user_info.get("given_name", ""),
            last_name=google_user_info.get("family_name", ""),
            preferred_first_name=google_user_info.get("given_name", ""),
            is_active=True,
            is_verified=True,
            password_hash=None,
        )
        db.put_item(user_item)
        user = UserItem(user_item)
        logger.info("New user created via Google OAuth", user_id=user.id, email=email)

    token_meta = set_auth_cookies(response, user.id)

    needs_agreement = not user.terms_accepted_at or not user.privacy_policy_accepted_at

    logger.info(
        "Google OAuth login successful",
        user_id=user.id,
        email=email,
        needs_agreement=needs_agreement,
    )

    return {**token_meta, "needs_agreement": needs_agreement}
