"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine
from app.core.config import settings
from app.core.secret_manager import get_database_url_from_secret, get_database_url_async_from_secret
from app.core.iam_auth import get_iam_db_connection_params
import structlog

logger = structlog.get_logger()

def _get_database_url() -> str:
    """Get database URL based on authentication method"""
    if settings.USE_IAM_DATABASE_AUTH and settings.DATABASE_HOST:
        logger.info("Using IAM database authentication")
        # For IAM auth, construct URL without password
        return f"postgresql://{settings.DATABASE_USER}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
    else:
        # Try to get URL from Secrets Manager first
        secret_url = get_database_url_from_secret()
        if secret_url:
            logger.info("Using database URL from Secrets Manager")
            return secret_url
        
        # Fall back to environment variables
        logger.info("Using database URL from environment variables")
        return settings.DATABASE_URL

def _get_database_url_async() -> str:
    """Get async database URL based on authentication method"""
    if settings.USE_IAM_DATABASE_AUTH and settings.DATABASE_HOST:
        logger.info("Using IAM database authentication (async)")
        return f"postgresql+asyncpg://{settings.DATABASE_USER}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
    else:
        # Try to get URL from Secrets Manager first
        secret_url = get_database_url_async_from_secret()
        if secret_url:
            logger.info("Using async database URL from Secrets Manager")
            return secret_url
        
        # Fall back to environment variables
        logger.info("Using async database URL from environment variables")
        return settings.DATABASE_URL_ASYNC

def _get_connection_args() -> dict:
    """Get connection arguments based on authentication method"""
    if settings.USE_IAM_DATABASE_AUTH and settings.DATABASE_HOST:
        return get_iam_db_connection_params(
            db_hostname=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            db_name=settings.DATABASE_NAME,
            db_username=settings.DATABASE_USER
        )
    return {}

# Create synchronous engine
engine = create_engine(
    _get_database_url(),
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG,
    connect_args=_get_connection_args()
)

# Create asynchronous engine
async_engine = create_async_engine(
    _get_database_url_async(),
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG,
    connect_args=_get_connection_args()
)

# Create session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Create base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """Dependency to get async database session"""
    async with AsyncSessionLocal() as session:
        yield session
