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
    
    logger.info(f"Fetching database credentials - Cache TTL: {cache_ttl}s, Secret ARN: {settings.DATABASE_CREDENTIALS_SECRET_ARN}")
    
    if _credentials_cache and (current_time - _cache_timestamp) < cache_ttl:
        cache_age = current_time - _cache_timestamp
        logger.info(f"Using cached database credentials (age: {cache_age:.1f}s)")
        logger.debug(f"Cached credentials: username={_credentials_cache.get('username', 'N/A')}, host={_credentials_cache.get('host', 'N/A')}")
        return _credentials_cache
    
    try:
        # Create Secrets Manager client
        logger.info(f"Creating Secrets Manager client for region: {settings.AWS_REGION}")
        secrets_client = boto3.client('secretsmanager', region_name=settings.AWS_REGION)
        
        # Get the secret value
        logger.info(f"Retrieving secret from AWS Secrets Manager: {settings.DATABASE_CREDENTIALS_SECRET_ARN}")
        response = secrets_client.get_secret_value(SecretId=settings.DATABASE_CREDENTIALS_SECRET_ARN)
        secret_data = json.loads(response['SecretString'])
        
        logger.info("Successfully retrieved database credentials from Secrets Manager")
        logger.debug(f"Secret data keys: {list(secret_data.keys())}")
        logger.debug(f"Secret contains username: {'username' in secret_data}, password: {'password' in secret_data}")
        logger.debug(f"Secret contains host: {'host' in secret_data}, port: {'port' in secret_data}, dbname: {'dbname' in secret_data}")
        
        # Handle secret format
        credentials = None
        if 'username' in secret_data and 'password' in secret_data:
            # Standard secret format with all fields
            if all(key in secret_data for key in ['host', 'port', 'dbname']):
                logger.info("Using complete secret format")
                credentials = {
                    'username': secret_data.get('username'),
                    'password': secret_data.get('password'),
                    'host': secret_data.get('host'),
                    'port': secret_data.get('port'),
                    'dbname': secret_data.get('dbname')
                }
                logger.debug(f"Complete secret credentials: username={credentials['username']}, host={credentials['host']}, port={credentials['port']}, dbname={credentials['dbname']}")
            else:
                # AWS managed master user password format (only username/password)
                logger.info("Using AWS managed master user password format - fetching connection details from settings")
                logger.debug(f"Settings: DATABASE_HOST={settings.DATABASE_HOST}, DATABASE_PORT={settings.DATABASE_PORT}, DATABASE_NAME={settings.DATABASE_NAME}")
                credentials = {
                    'username': secret_data.get('username'),
                    'password': secret_data.get('password'),
                    'host': settings.DATABASE_HOST,
                    'port': settings.DATABASE_PORT,
                    'dbname': settings.DATABASE_NAME
                }
                logger.debug(f"AWS managed secret credentials: username={credentials['username']}, host={credentials['host']}, port={credentials['port']}, dbname={credentials['dbname']}")
        else:
            logger.error(f"Unexpected secret format. Available keys: {list(secret_data.keys())}")
            return None
        
        # Cache the credentials
        if credentials:
            _credentials_cache = credentials
            _cache_timestamp = current_time
            logger.info(f"Cached database credentials for {cache_ttl} seconds")
            logger.debug(f"Final credentials: username={credentials['username']}, host={credentials['host']}, port={credentials['port']}, dbname={credentials['dbname']}")
        else:
            logger.warning("No credentials constructed from secret data")
        
        return credentials
        
    except Exception as e:
        logger.error("Failed to retrieve database credentials from Secrets Manager", 
                    error=str(e), 
                    secret_arn=settings.DATABASE_CREDENTIALS_SECRET_ARN)
        return None

def get_database_url_from_secret() -> Optional[str]:
    """
    Construct database URL using credentials from Secrets Manager
    """
    logger.info("Constructing database URL from secret")
    credentials = get_database_credentials_from_secret()
    if not credentials or not credentials.get('username') or not credentials.get('password'):
        logger.warning("Could not get credentials from secret, falling back to environment variables")
        return None

    # Use host, port, and dbname from secret if available, otherwise fall back to settings
    host = credentials.get('host') or settings.DATABASE_HOST
    port = credentials.get('port') or settings.DATABASE_PORT
    dbname = credentials.get('dbname') or settings.DATABASE_NAME

    logger.debug(f"Database connection details: host={host}, port={port}, dbname={dbname}, username={credentials['username']}")

    # Construct the database URL with SSL requirement
    database_url = f"postgresql://{credentials['username']}:{credentials['password']}@{host}:{port}/{dbname}?sslmode=require"
    logger.info(f"Constructed database URL: postgresql://{credentials['username']}:***@{host}:{port}/{dbname}?sslmode=require")
    return database_url

def get_database_url_async_from_secret() -> Optional[str]:
    """
    Construct async database URL using credentials from Secrets Manager
    """
    logger.info("Constructing async database URL from secret")
    credentials = get_database_credentials_from_secret()
    if not credentials or not credentials.get('username') or not credentials.get('password'):
        logger.warning("Could not get credentials from secret, falling back to environment variables")
        return None

    # Use host, port, and dbname from secret if available, otherwise fall back to settings
    host = credentials.get('host') or settings.DATABASE_HOST
    port = credentials.get('port') or settings.DATABASE_PORT
    dbname = credentials.get('dbname') or settings.DATABASE_NAME

    logger.debug(f"Async database connection details: host={host}, port={port}, dbname={dbname}, username={credentials['username']}")

    # Construct the async database URL with SSL requirement
    database_url_async = f"postgresql+asyncpg://{credentials['username']}:{credentials['password']}@{host}:{port}/{dbname}?sslmode=require"
    logger.info(f"Constructed async database URL: postgresql+asyncpg://{credentials['username']}:***@{host}:{port}/{dbname}?sslmode=require")
    return database_url_async

def clear_credentials_cache():
    """
    Clear the cached credentials (useful for testing or when credentials change)
    """
    global _credentials_cache, _cache_timestamp
    _credentials_cache = {}
    _cache_timestamp = 0
    logger.info("Cleared database credentials cache")

