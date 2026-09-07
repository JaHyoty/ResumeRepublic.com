"""
ResumeRepublic Backend API
Main FastAPI application entry point — DynamoDB serverless version
"""
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog
import logging
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.settings import settings
from app.core.limiter import limiter
from app.core.dynamodb import DynamoDBClient, get_db
from app.api import auth, esc, resume, user, applications, job_posting, webhooks

# Configure structured logging
if settings.ENVIRONMENT == "development":
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer(colors=True)
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
else:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()

# Set standard logging level
if settings.ENVIRONMENT == "development":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

# Create FastAPI application
app = FastAPI(
    title="ResumeRepublic API",
    description="Career management and resume optimization platform",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT == "development" else None,
)

# Add rate limit exception handler and middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Maximum request body size (6MB, matching Lambda / API Gateway limit)
MAX_BODY_SIZE = 6 * 1024 * 1024


@app.middleware("http")
async def limit_request_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_BODY_SIZE:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request entity too large (max 6MB)"},
                )
        except ValueError:
            pass
    return await call_next(request)


# Add CORS middleware (credentials allowed only if wildcard is not in origins)
has_wildcard = "*" in settings.ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=not has_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Only add TrustedHostMiddleware if we have specific hosts configured
if (settings.ALLOWED_HOSTS and
    len(settings.ALLOWED_HOSTS) > 0 and
    not any("*" in host for host in settings.ALLOWED_HOSTS)):
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(user.router, prefix="/api/user", tags=["user"])
app.include_router(esc.router, prefix="/api/esc", tags=["experience-skills-catalog"])
app.include_router(resume.router, prefix="/api/resume", tags=["resume"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(job_posting.router, prefix="/api/job-postings", tags=["job-postings"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "ResumeRepublic API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check(db: DynamoDBClient = Depends(get_db)):
    """Health check with DynamoDB connectivity test"""
    db_status = "unknown"
    try:
        # Simple connectivity test: try to read the counter item
        db.get_item("COUNTER", "user")
        db_status = "connected"
    except Exception as e:
        logger.error("DynamoDB connection check failed", error=str(e))
        db_status = "connection_failed"

    response_data = {
        "status": "healthy" if db_status == "connected" else "degraded",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "database": f"dynamodb ({db_status})",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if settings.ENVIRONMENT == "development":
        response_data["table"] = settings.DYNAMODB_TABLE_NAME
    return response_data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
