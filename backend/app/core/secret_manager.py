"""
AWS Secrets Manager integration for fetching database credentials
"""
import json
import boto3
import structlog
from typing import Dict, Optional
from app.core.config import settings

logger = structlog.get_logger()

def get_database_credentials_from_secret() -> Optional[Dict[str, str]]:
    """
    Fetch database credentials from AWS Secrets Manager
    Returns a dictionary with 'username' and 'password' keys
    """
    if not settings.DATABASE_CREDENTIALS_SECRET_ARN:
        logger.warning("No DATABASE_CREDENTIALS_SECRET_ARN provided, using environment variables")
        return None
    
    try:
        # Create Secrets Manager client
        secrets_client = boto3.client('secretsmanager', region_name=settings.AWS_REGION)
        
        # Get the secret value
        response = secrets_client.get_secret_value(SecretId=settings.DATABASE_CREDENTIALS_SECRET_ARN)
        secret_data = json.loads(response['SecretString'])
        
        logger.info("Successfully retrieved database credentials from Secrets Manager")
        
        # Handle both custom secret format and RDS managed secret format
        if 'username' in secret_data and 'password' in secret_data:
            # Custom secret format
            logger.info("Using custom secret format")
            return {
                'username': secret_data.get('username'),
                'password': secret_data.get('password'),
                'host': secret_data.get('host'),
                'port': secret_data.get('port'),
                'dbname': secret_data.get('dbname')
            }
        elif 'masterUsername' in secret_data and 'masterPassword' in secret_data:
            # RDS managed secret format
            logger.info("Using RDS managed secret format")
            return {
                'username': secret_data.get('masterUsername'),
                'password': secret_data.get('masterPassword'),
                'host': secret_data.get('host'),
                'port': secret_data.get('port'),
                'dbname': secret_data.get('dbname')
            }
        else:
            logger.error(f"Unexpected secret format. Available keys: {list(secret_data.keys())}")
            return None
        
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
    logger.info("Constructed database URL from Secrets Manager credentials")
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
    logger.info("Constructed async database URL from Secrets Manager credentials")
    return database_url_async
