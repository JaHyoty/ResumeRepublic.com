"""
Database configuration and session management
"""

from sqlalchemy import create_engine, text
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
import asyncio
import threading
from typing import Optional

logger = structlog.get_logger()

# Global lock to prevent concurrent refresh attempts
_refresh_lock = threading.Lock()
_is_refreshing = False
_last_refresh_time = 0

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
            logger.warning("Database authentication error detected, clearing credentials cache and refreshing connections")
            clear_credentials_cache()
            refresh_database_engines()

def refresh_database_engines():
    """
    Refresh database engines with new credentials from Secrets Manager
    """
    global engine, async_engine, SessionLocal, AsyncSessionLocal, _is_refreshing
    
    try:
        logger.info("Refreshing database engines with new credentials")
        
        # Get new database URLs
        new_database_url = _get_database_url()
        new_async_database_url = _get_database_url_async()
        
        # Store old engines for disposal
        old_engine = engine if 'engine' in globals() else None
        old_async_engine = async_engine if 'async_engine' in globals() else None
        
        # Create new engines first
        new_engine = create_engine(
            new_database_url,
            pool_pre_ping=True,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            echo=settings.DEBUG,
            connect_args=_get_connection_args()
        )
        
        new_async_engine = create_async_engine(
            new_async_database_url,
            pool_pre_ping=True,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            echo=settings.DEBUG,
            connect_args=_get_connection_args()
        )
        
        # Atomically replace the global engines
        engine = new_engine
        async_engine = new_async_engine
        logger.info(f"Global engine updated: {id(engine)}")
        
        # Recreate session makers with new engines
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        AsyncSessionLocal = async_sessionmaker(
            async_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        logger.info("Successfully refreshed database engines with new credentials")
        
        # Dispose old engines after new ones are ready
        if old_engine:
            try:
                old_engine.dispose()
                logger.info("Disposed old synchronous engine")
            except Exception as e:
                logger.warning("Failed to dispose old synchronous engine", error=str(e))
        
        if old_async_engine:
            try:
                # For async engine disposal, we need to handle it carefully
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Schedule disposal for later
                        asyncio.create_task(old_async_engine.dispose())
                    else:
                        loop.run_until_complete(old_async_engine.dispose())
                except RuntimeError:
                    # If no event loop, create one
                    asyncio.run(old_async_engine.dispose())
                logger.info("Disposed old asynchronous engine")
            except Exception as e:
                logger.warning("Failed to dispose old asynchronous engine", error=str(e))
        
    except Exception as e:
        logger.error(f"Failed to refresh database engines: {e}")
        raise
    finally:
        _is_refreshing = False

def force_refresh_database_engines():
    """
    Force refresh database engines - only called internally on authentication errors
    Thread-safe version that prevents concurrent refresh attempts
    """
    global _is_refreshing, _last_refresh_time
    import time
    
    current_time = time.time()
    
    # Check if already refreshing
    if _is_refreshing:
        logger.info("Database refresh already in progress, skipping duplicate request")
        return
    
    # Prevent rapid successive refresh attempts (minimum 5 seconds between refreshes)
    if current_time - _last_refresh_time < 5:
        logger.info("Database refresh attempted too soon, skipping duplicate request")
        return
    
    with _refresh_lock:
        if _is_refreshing:
            logger.info("Database refresh already in progress (double-check), skipping duplicate request")
            return
        
        _is_refreshing = True
        try:
            logger.info("Force refreshing database engines due to authentication error")
            clear_credentials_cache()
            refresh_database_engines()
            _last_refresh_time = current_time
        except Exception as e:
            logger.error("Failed to force refresh database engines", error=str(e))
            raise
        finally:
            _is_refreshing = False

def validate_database_connection() -> bool:
    """
    Validate that the current database connection works
    """
    try:
        # Use the global engine variable that should be updated after refresh
        logger.debug(f"Validating connection with engine: {id(engine)}")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.debug("Database connection validation successful")
            return True
    except Exception as e:
        logger.warning("Database connection validation failed", error=str(e))
        return False

def is_refresh_in_progress() -> bool:
    """
    Check if a database refresh is currently in progress
    """
    return _is_refreshing

def _get_database_url() -> str:
    """Get database URL based on authentication method"""
    if settings.USE_IAM_DATABASE_AUTH and settings.DATABASE_HOST:
        logger.info("Using IAM database authentication")
        # For IAM auth, construct URL without password
        iam_url = f"postgresql://{settings.DATABASE_USER}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
        logger.debug(f"IAM database URL: {iam_url}")
        return iam_url
    else:
        # Try to get URL from Secrets Manager first
        logger.info(f"Attempting to get database URL from Secrets Manager (ARN: {settings.DATABASE_CREDENTIALS_SECRET_ARN})")
        secret_url = get_database_url_from_secret()
        if secret_url:
            logger.info("Successfully obtained database URL from secret")
            return secret_url

        # Fall back to environment variables
        logger.info("Using database URL from environment variables")
        logger.debug(f"Environment DATABASE_URL: {settings.DATABASE_URL}")
        return settings.DATABASE_URL

def _get_database_url_async() -> str:
    """Get async database URL based on authentication method"""
    if settings.USE_IAM_DATABASE_AUTH and settings.DATABASE_HOST:
        logger.info("Using IAM database authentication (async)")
        iam_url_async = f"postgresql+asyncpg://{settings.DATABASE_USER}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
        logger.debug(f"IAM async database URL: {iam_url_async}")
        return iam_url_async
    else:
        # Try to get URL from Secrets Manager first
        logger.info(f"Attempting to get async database URL from Secrets Manager (ARN: {settings.DATABASE_CREDENTIALS_SECRET_ARN})")
        secret_url = get_database_url_async_from_secret()
        if secret_url:
            logger.info("Successfully obtained async database URL from secret")
            return secret_url

        # Fall back to environment variables
        logger.info("Using async database URL from environment variables")
        logger.debug(f"Environment DATABASE_URL_ASYNC: {settings.DATABASE_URL_ASYNC}")
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
    
    # Always require SSL for RDS connections
    return {
        "sslmode": "require"
    }

# Create synchronous engine
database_url = _get_database_url()
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    echo=settings.DEBUG,
    connect_args=_get_connection_args()
)

# Note: handle_error event listener removed due to SQLAlchemy 2.0 compatibility issues
# The error handling is now done in the health check endpoint

# Create asynchronous engine
async_database_url = _get_database_url_async()
async_engine = create_async_engine(
    async_database_url,
    pool_pre_ping=True,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    echo=settings.DEBUG,
    connect_args=_get_connection_args()
)

# Note: async handle_error event listener removed due to SQLAlchemy 2.0 compatibility issues
# The error handling is now done in the health check endpoint

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
