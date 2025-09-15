"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine
from app.core.settings import settings
from app.core.secret_manager import get_database_url_from_secret, get_database_url_async_from_secret, clear_credentials_cache
from app.core.iam_auth import get_iam_db_connection_params
import structlog
from sqlalchemy import event

logger = structlog.get_logger()

def _handle_db_error(conn, branch):
    """
    Handle database connection errors and invalidate cache if authentication fails
    """
    try:
        # This will be called when there's a connection error
        pass
    except Exception as e:
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['authentication', 'password', 'login', 'access denied', 'fatal: password authentication failed']):
            logger.warning("Database authentication error detected, clearing credentials cache")
            clear_credentials_cache()

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
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    echo=settings.DEBUG,
    connect_args=_get_connection_args()
)

# Add event listener for connection errors
@event.listens_for(engine, "handle_error")
def handle_db_error(conn, branch, err, errno, statement, parameters, context, orig):
    _handle_db_error(conn, branch)

# Create asynchronous engine
async_engine = create_async_engine(
    _get_database_url_async(),
    pool_pre_ping=True,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    echo=settings.DEBUG,
    connect_args=_get_connection_args()
)

# Add event listener for async connection errors
@event.listens_for(async_engine.sync_engine, "handle_error")
def handle_async_db_error(conn, branch, err, errno, statement, parameters, context, orig):
    _handle_db_error(conn, branch)

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
