"""
AWS Secrets Manager integration for fetching database credentials
"""
import json
import boto3
import structlog
import time
from typing import Dict, Optional
from app.core.settings import settings

logger = structlog.get_logger()

# Cache for database credentials
_credentials_cache = {}
_cache_timestamp = 0

def get_database_credentials_from_secret() -> Optional[Dict[str, str]]:
    """
    Fetch database credentials from AWS Secrets Manager with caching
    Returns a dictionary with 'username' and 'password' keys
    """
    global _credentials_cache, _cache_timestamp
    
    if not settings.DATABASE_CREDENTIALS_SECRET_ARN:
        logger.warning("No DATABASE_CREDENTIALS_SECRET_ARN provided, using environment variables")
        return None
    
    # Check if we have valid cached credentials
    current_time = time.time()
    cache_ttl = settings.DATABASE_CREDENTIALS_CACHE_TTL
    if _credentials_cache and (current_time - _cache_timestamp) < cache_ttl:
        logger.info("Using cached database credentials (cache hit)")
        return _credentials_cache
    
    try:
        # Create Secrets Manager client
        secrets_client = boto3.client('secretsmanager', region_name=settings.AWS_REGION)
        
        # Get the secret value
        response = secrets_client.get_secret_value(SecretId=settings.DATABASE_CREDENTIALS_SECRET_ARN)
        secret_data = json.loads(response['SecretString'])
        
        logger.info("Successfully retrieved database credentials from Secrets Manager")
        
        # Handle secret format (RDS managed secrets use username/password)
        credentials = None
        if 'username' in secret_data and 'password' in secret_data:
            # RDS managed secret format (uses username/password, not masterUsername/masterPassword)
            logger.info("Using RDS managed secret format")
            credentials = {
                'username': secret_data.get('username'),
                'password': secret_data.get('password'),
                'host': secret_data.get('host'),
                'port': secret_data.get('port'),
                'dbname': secret_data.get('dbname')
            }
        else:
            logger.error(f"Unexpected secret format. Available keys: {list(secret_data.keys())}")
            return None
        
        # Cache the credentials
        if credentials:
            _credentials_cache = credentials
            _cache_timestamp = current_time
            logger.info(f"Cached database credentials for {cache_ttl} seconds")
        
        return credentials
        
    except Exception as e:
        logger.error("Failed to retrieve database credentials from Secrets Manager", error=str(e))
        return None

def get_database_url_from_secret() -> Optional[str]:
    """
    Construct database URL using credentials from Secrets Manager
    """
    credentials = get_database_credentials_from_secret()
    if not credentials or not credentials.get('username') or not credentials.get('password'):
        logger.warning("Could not get credentials from secret, falling back to environment variables")
        return None

    # Use host, port, and dbname from secret if available, otherwise fall back to settings
    host = credentials.get('host') or settings.DATABASE_HOST
    port = credentials.get('port') or settings.DATABASE_PORT
    dbname = credentials.get('dbname') or settings.DATABASE_NAME

    # Construct the database URL
    database_url = f"postgresql://{credentials['username']}:{credentials['password']}@{host}:{port}/{dbname}"
    return database_url

def get_database_url_async_from_secret() -> Optional[str]:
    """
    Construct async database URL using credentials from Secrets Manager
    """
    credentials = get_database_credentials_from_secret()
    if not credentials or not credentials.get('username') or not credentials.get('password'):
        logger.warning("Could not get credentials from secret, falling back to environment variables")
        return None

    # Use host, port, and dbname from secret if available, otherwise fall back to settings
    host = credentials.get('host') or settings.DATABASE_HOST
    port = credentials.get('port') or settings.DATABASE_PORT
    dbname = credentials.get('dbname') or settings.DATABASE_NAME

    # Construct the async database URL
    database_url_async = f"postgresql+asyncpg://{credentials['username']}:{credentials['password']}@{host}:{port}/{dbname}"
    return database_url_async

def clear_credentials_cache():
    """
    Clear the cached credentials (useful for testing or when credentials change)
    """
    global _credentials_cache, _cache_timestamp
    _credentials_cache = {}
    _cache_timestamp = 0
    logger.info("Cleared database credentials cache")

