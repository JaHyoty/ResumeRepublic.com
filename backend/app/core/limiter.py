from fastapi import Request
from jose import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.settings import settings


def get_user_key(request: Request) -> str:
    """Custom key function for rate limiting (by authenticated user ID or remote IP)."""
    try:
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        if token:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
    except Exception:
        pass
    # Check X-Forwarded-For header first (standard for API Gateway / Lambda)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    return get_remote_address(request)


limiter = Limiter(key_func=get_user_key)
