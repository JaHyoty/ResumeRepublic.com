"""
AWS Secrets Manager integration for fetching database credentials
"""
import json
import boto3
import structlog
from functools import lru_cache
from typing import Dict, Optional
from app.core.settings import settings

logger = structlog.get_logger()

@lru_cache(maxsize=1)
def get_database_credentials_from_secret() -> Optional[Dict[str, str]]:
    """
    Fetch database credentials from AWS Secrets Manager with LRU caching
    Returns a dictionary with 'username' and 'password' keys
    """
    if not settings.DATABASE_CREDENTIALS_SECRET_ARN:
        logger.warning("No DATABASE_CREDENTIALS_SECRET_ARN provided, using environment variables")
        return None
    
    logger.info(f"Fetching database credentials from Secrets Manager - Secret ARN: {settings.DATABASE_CREDENTIALS_SECRET_ARN}")
    
    try:
        # Create Secrets Manager client
        logger.info(f"Creating Secrets Manager client for region: {settings.AWS_REGION}")
        secrets_client = boto3.client('secretsmanager', region_name=settings.AWS_REGION)
        
        # Get the secret value
        logger.info(f"Retrieving secret from AWS Secrets Manager: {settings.DATABASE_CREDENTIALS_SECRET_ARN}")
        response = secrets_client.get_secret_value(SecretId=settings.DATABASE_CREDENTIALS_SECRET_ARN)
        secret_data = json.loads(response['SecretString'])
        
        # Parse the secret data based on format
        credentials = None
        if 'username' in secret_data and 'password' in secret_data:
            # Direct username/password format
            credentials = {
                'username': secret_data.get('username'),
                'password': secret_data.get('password'),
                'host': settings.DATABASE_HOST,
                'port': settings.DATABASE_PORT,
                'dbname': settings.DATABASE_NAME
            }
            logger.debug(f"Direct credentials format: username={credentials['username']}, host={credentials['host']}, port={credentials['port']}, dbname={credentials['dbname']}")
        elif 'engine' in secret_data and secret_data.get('engine') == 'postgres':
            # AWS managed secret format
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
        
        if credentials:
            logger.info(f"Successfully retrieved database credentials from Secrets Manager")
            logger.debug(f"Final credentials: username={credentials['username']}, host={credentials['host']}, port={credentials['port']}, dbname={credentials['dbname']}")
        else:
            logger.warning("No credentials constructed from secret data")
        
        return credentials
        
    except Exception as e:
        logger.error("Failed to retrieve database credentials from Secrets Manager", error=str(e))
        return None

def clear_credentials_cache():
    """Clear the cached database credentials"""
    get_database_credentials_from_secret.cache_clear()
    logger.info("Cleared database credentials cache")

def get_database_url_from_secret() -> Optional[str]:
    """
    Get database URL from Secrets Manager credentials
    Returns a PostgreSQL connection URL or None if credentials are not available
    """
    credentials = get_database_credentials_from_secret()
    if not credentials:
        logger.warning("Could not get credentials from secret, falling back to environment variables")
        return None
    
    # Construct database URL
    username = credentials.get('username')
    password = credentials.get('password')
    host = credentials.get('host')
    port = credentials.get('port')
    dbname = credentials.get('dbname')
    
    if not all([username, password, host, port, dbname]):
        logger.error(f"Missing required credentials: username={bool(username)}, password={bool(password)}, host={bool(host)}, port={bool(port)}, dbname={bool(dbname)}")
        return None
    
    database_url = f"postgresql://{username}:{password}@{host}:{port}/{dbname}"
    logger.info("Successfully constructed database URL from secret")
    logger.debug(f"Database URL constructed: postgresql://{username}:***@{host}:{port}/{dbname}")
    
    return database_url