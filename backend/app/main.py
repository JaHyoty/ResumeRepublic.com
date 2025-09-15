"""
CareerPathPro Backend API
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
import structlog
import logging

from app.core.settings import settings
from app.core.secret_manager import clear_credentials_cache
from app.core.database import engine
from app.api import auth, esc, resume, user, applications

# Configure structured logging
if settings.ENVIRONMENT == "development":
    # Development: Human-readable format to console
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
    # Production: JSON format
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

# Configure standard Python logging for development
if settings.ENVIRONMENT == "development":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # Output to console
        ]
    )

# Create FastAPI application
app = FastAPI(
    title="ResumeRepublic API",
    description="Career management and resume optimization platform",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Only add TrustedHostMiddleware if we have specific hosts configured and no wildcards
# Skip in containerized environments where ALB health checks come from internal IPs
if (settings.ALLOWED_HOSTS and 
    len(settings.ALLOWED_HOSTS) > 0 and 
    not any("*" in host for host in settings.ALLOWED_HOSTS) and
    not any("elb.amazonaws.com" in host for host in settings.ALLOWED_HOSTS)):
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



@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "ResumeRepublic API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Detailed health check with database migration status"""
    logger = structlog.get_logger()
    
    # Check database connection and migration status
    db_status = "unknown"
    try:
        # Use the existing engine from database module instead of creating a new one
        with engine.connect() as conn:
            # Check if alembic_version table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'alembic_version'
                )
            """))
            has_alembic_table = result.fetchone()[0]
            
            if has_alembic_table:
                # Get current migration version
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                current_version = result.fetchone()[0] if result.rowcount > 0 else "unknown"
                db_status = f"migrated (version: {current_version})"
            else:
                db_status = "no_migrations"
                
    except Exception as e:
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['authentication', 'password', 'login', 'access denied', 'fatal: password authentication failed']):
            logger.warning("Database authentication error detected, clearing credentials cache", error=str(e))
            clear_credentials_cache()
        else:
            logger.warning("Database health check failed", error=str(e))
        db_status = "error"
    
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "database": db_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
