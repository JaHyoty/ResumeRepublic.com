"""
Authentication utilities — dual-cookie (access + refresh) token strategy.
DynamoDB version: uses DynamoDB client instead of SQLAlchemy session.
"""

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
import structlog

from app.core.dynamodb import DynamoDBClient, get_db
from app.core.settings import settings
from app.core.dynamodb_models import UserItem

logger = structlog.get_logger()
security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a short-lived JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a long-lived JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------

def verify_token(token: str, expected_type: Optional[str] = None) -> Optional[dict]:
    """Verify a JWT token and optionally check the token type claim."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if expected_type and payload.get("type") != expected_type:
            logger.warning("Token type mismatch", expected=expected_type, got=payload.get("type"))
            return None
        return payload
    except JWTError as e:
        logger.warning("JWT verification failed", error=str(e))
        return None


# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------

def set_auth_cookies(response: Response, user_id: int) -> dict:
    """Create access + refresh tokens and set them as httpOnly cookies."""
    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token = create_refresh_token(data={"sub": str(user_id)})
    cookie_domain = settings.COOKIE_DOMAIN if settings.COOKIE_DOMAIN else None

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=cookie_domain,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=cookie_domain,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/auth",
    )

    return {
        "token_type": "cookie",
        "access_token_expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token_expires_in": settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    }


def clear_auth_cookies(response: Response) -> None:
    """Delete both auth cookies with matching security and samesite attributes."""
    cookie_domain = settings.COOKIE_DOMAIN if settings.COOKIE_DOMAIN else None
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=cookie_domain,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth",
        domain=cookie_domain,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )
    # Also delete refresh_token at root path in case it was set there
    response.delete_cookie(
        key="refresh_token",
        path="/",
        domain=cookie_domain,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )


# ---------------------------------------------------------------------------
# Dependency: extract current user from cookies (with Bearer fallback)
# ---------------------------------------------------------------------------

def _extract_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials],
) -> Optional[str]:
    """Try cookie first, fall back to Authorization header."""
    token = request.cookies.get("access_token")
    if token:
        return token
    if credentials:
        return credentials.credentials
    return None


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: DynamoDBClient = Depends(get_db),
) -> UserItem:
    """Get current user from access_token cookie or Bearer header."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = _extract_token(request, credentials)
    if not token:
        raise credentials_exception

    payload = verify_token(token, expected_type="access")
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Fetch user from DynamoDB
    user_data = db.get_item(f"USER#{user_id}", "PROFILE")
    if user_data is None:
        raise credentials_exception

    return UserItem(user_data)


def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: DynamoDBClient = Depends(get_db),
) -> Optional[UserItem]:
    """Get current user, returns None if not authenticated."""
    token = _extract_token(request, credentials)
    if not token:
        return None

    try:
        payload = verify_token(token, expected_type="access")
        if payload is None:
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
        user_data = db.get_item(f"USER#{user_id}", "PROFILE")
        if user_data is None:
            return None
        return UserItem(user_data)
    except JWTError:
        return None
