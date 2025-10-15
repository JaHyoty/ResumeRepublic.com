"""
Database configuration and session management with self-healing capabilities
"""
import threading
import time
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine, text, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
import structlog

from app.core.settings import settings
from app.core.secret_manager import get_database_url_from_secret, clear_credentials_cache

logger = structlog.get_logger()

# Global variables for engine and session maker
engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None
Base = declarative_base()

# Global lock to prevent concurrent refresh attempts
_refresh_lock = threading.Lock()
_is_refreshing = False
_last_refresh_time = 0

def _get_connection_args():
    """Get connection arguments for database connections"""
    # Always require SSL for RDS connections
    return {
        "sslmode": "require"
    }

def _get_database_url() -> str:
    """Get database URL from Secrets Manager or environment variables"""
    # Try to get URL from Secrets Manager first
    secret_url = get_database_url_from_secret()
    if secret_url:
        logger.info("Successfully obtained database URL from secret manager")
        return secret_url

    # Fall back to environment variables
    logger.info("Using database URL from environment variables")
    logger.debug(f"Environment DATABASE_URL: {settings.DATABASE_URL}")
    
    return settings.DATABASE_URL

def refresh_engines_with_fresh_credentials():
    """Refresh database engine with fresh credentials from Secrets Manager"""
    global engine, SessionLocal, _is_refreshing, _last_refresh_time
    
    with _refresh_lock:
        # Prevent concurrent refresh attempts
        if _is_refreshing:
            logger.info("Database refresh already in progress, skipping")
            return
        
        # Rate limiting: don't refresh more than once per minute
        current_time = time.time()
        if current_time - _last_refresh_time < 60:
            logger.info("Database refresh rate limited, skipping")
            return
        
        _is_refreshing = True
        _last_refresh_time = current_time
    
    try:
        logger.info("Starting database engine refresh with fresh credentials")
        
        # Clear credentials cache to force fresh fetch
        clear_credentials_cache()
        
        # Store old engine for disposal
        old_engine = engine
        
        # Create new engine with fresh credentials
        database_url = _get_database_url()
        
        new_engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            echo=settings.DEBUG,
            connect_args=_get_connection_args(),
            echo_pool=True
        )
        
        # Atomically replace the global engine
        engine = new_engine
        
        # Recreate session maker with new engine
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        logger.info("Successfully refreshed database engine with fresh credentials")
        
        # Dispose old engine after new one is ready
        if old_engine:
            try:
                old_engine.dispose()
                logger.debug("Disposed old engine")
            except Exception as e:
                logger.warning("Failed to dispose old engine", error=str(e))
                
    except Exception as e:
        logger.error("Failed to refresh database engines", error=str(e))
        raise e
    finally:
        with _refresh_lock:
            _is_refreshing = False

def is_refresh_in_progress() -> bool:
    """Check if a database refresh is currently in progress"""
    return _is_refreshing

# Initialize engine and session maker
logger.info("Initializing database engine")
database_url = _get_database_url()
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    echo=settings.DEBUG,
    connect_args=_get_connection_args(),
    echo_pool=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger.info("Database engine initialized successfully")

def get_db():
    """Dependency to get database session with automatic retry on authentication failure"""
    db = None
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['password authentication failed', 'fatal: password authentication failed', 'authentication', 'login', 'access denied']):
            logger.warning("Authentication error detected in get_db, refreshing credentials and retrying", error=str(e))
            
            # Close the failed session
            if db:
                db.close()
            
            try:
                # Refresh credentials and retry
                refresh_engines_with_fresh_credentials()
                
                # Create new session with refreshed credentials
                db = SessionLocal()
                yield db
                logger.info("Successfully retried get_db after credential refresh")
            except Exception as retry_error:
                logger.error("Retry after credential refresh also failed", error=str(retry_error))
                if db:
                    db.close()
                raise retry_error
        else:
            # Re-raise non-authentication errors
            if db:
                db.close()
            raise e
    finally:
        if db:
            db.close()

# Async database dependency removed - not used in this application

@contextmanager
def get_db_for_background_task():
    """
    Context manager for background tasks to get database connections with automatic retry on authentication failure
    """
    db = None
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['password authentication failed', 'fatal: password authentication failed', 'authentication', 'login', 'access denied']):
            logger.warning("Authentication error detected in get_db_for_background_task, refreshing credentials and retrying", error=str(e))
            
            # Close the failed session
            if db:
                db.close()
            
            try:
                # Refresh credentials and retry
                refresh_engines_with_fresh_credentials()
                
                # Create new session with refreshed credentials
                db = SessionLocal()
                yield db
                logger.info("Successfully retried get_db_for_background_task after credential refresh")
            except Exception as retry_error:
                logger.error("Retry after credential refresh also failed", error=str(retry_error))
                if db:
                    db.close()
                raise retry_error
        else:
            # Re-raise non-authentication errors
            if db:
                db.close()
            raise e
    finally:
        if db:
            db.close()