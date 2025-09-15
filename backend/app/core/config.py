"""
Configuration System
Handles both local development (env files) and cloud deployment (infrastructure outputs)
"""
import os
import logging
from typing import Optional, Dict, Any
from functools import lru_cache

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception

logger = logging.getLogger(__name__)

class Config:
    """
    Configuration system that handles:
    1. Local development: Environment variables from .env files
    2. Cloud deployment: SSM parameters from infrastructure
    3. Fallback: Default values
    """
    
    def __init__(self):
        self.project_name = os.getenv("PROJECT_NAME", "resumerepublic")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.is_cloud_deployment = self._is_cloud_deployment()
        
        # Initialize SSM client only for cloud deployments
        self.ssm_client = None
        if self.is_cloud_deployment and BOTO3_AVAILABLE:
            try:
                self.ssm_client = boto3.client('ssm')
                logger.info("SSM client initialized for cloud deployment")
            except (NoCredentialsError, Exception) as e:
                logger.warning(f"Failed to initialize SSM client: {e}")
                self.ssm_client = None
    
    def _is_cloud_deployment(self) -> bool:
        """Determine if we're in a cloud deployment environment"""
        # Check for cloud deployment indicators
        cloud_indicators = [
            os.getenv("AWS_EXECUTION_ENV"),  # ECS/Lambda
            os.getenv("ECS_CONTAINER_METADATA_URI"),  # ECS
            os.getenv("AWS_LAMBDA_FUNCTION_NAME"),  # Lambda
            os.getenv("USE_SSM_PARAMETERS", "").lower() == "true",  # Explicit flag
            self.environment in ["production", "staging"]  # Environment-based
        ]
        return any(cloud_indicators)
    
    def get_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get configuration value with unified priority:
        1. Pydantic settings (loads .env files and environment variables)
        2. SSM parameter (for cloud deployment)
        3. Default value
        """
        # First try Pydantic settings (handles .env files and environment variables)
        try:
            from app.core.settings import settings
            settings_value = getattr(settings, key, None)
            if settings_value:
                logger.debug(f"Using Pydantic settings for {key}")
                return settings_value
        except Exception as e:
            logger.debug(f"Could not access Pydantic settings: {e}")
        
        # Try SSM parameter if in cloud deployment
        if self.is_cloud_deployment and self.ssm_client:
            ssm_value = self._get_ssm_parameter(key)
            if ssm_value:
                logger.debug(f"Using SSM parameter for {key}")
                return ssm_value
        
        # Return default
        logger.debug(f"Using default value for {key}")
        return default
    
    def _get_ssm_parameter(self, key: str) -> Optional[str]:
        """Get parameter from SSM Parameter Store"""
        if not self.ssm_client:
            return None
        
        # Map configuration keys to SSM parameter paths
        ssm_paths = {
            # OpenRouter
            "OPENROUTER_API_KEY": f"/{self.project_name}/{self.environment}/openrouter/api_key",
            "OPENROUTER_LLM_MODEL": f"/{self.project_name}/{self.environment}/app/openrouter_llm_model",
            
            # Application
            "SECRET_KEY": f"/{self.project_name}/{self.environment}/app/secret_key",
            
            # Database
            "DATABASE_HOST": f"/{self.project_name}/{self.environment}/database/host",
            "DATABASE_NAME": f"/{self.project_name}/{self.environment}/database/name",
            "DATABASE_USER": f"/{self.project_name}/{self.environment}/database/user",
            "DATABASE_PASSWORD": f"/{self.project_name}/{self.environment}/database/password",
            
            # OAuth
            "GOOGLE_CLIENT_ID": f"/{self.project_name}/{self.environment}/google/client_id",
            "GOOGLE_CLIENT_SECRET": f"/{self.project_name}/{self.environment}/google/client_secret",
            "GITHUB_CLIENT_ID": f"/{self.project_name}/{self.environment}/github/client_id",
            "GITHUB_CLIENT_SECRET": f"/{self.project_name}/{self.environment}/github/client_secret",
            
            # SSL/TLS
            "SSL_CIPHER_SUITES": f"/{self.project_name}/{self.environment}/app/ssl_cipher_suites",
            "MIN_TLS_VERSION": f"/{self.project_name}/{self.environment}/app/min_tls_version",
        }
        
        ssm_path = ssm_paths.get(key)
        if not ssm_path:
            return None
        
        try:
            response = self.ssm_client.get_parameter(
                Name=ssm_path,
                WithDecryption=True
            )
            return response['Parameter']['Value']
        except ClientError as e:
            if e.response['Error']['Code'] != 'ParameterNotFound':
                logger.warning(f"Error retrieving SSM parameter {ssm_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error retrieving SSM parameter {ssm_path}: {e}")
            return None
    
    # Configuration properties with unified access
    @property
    def openrouter_api_key(self) -> Optional[str]:
        return self.get_value("OPENROUTER_API_KEY")
    
    @property
    def openrouter_llm_model(self) -> Optional[str]:
        return self.get_value("OPENROUTER_LLM_MODEL", "anthropic/claude-3.5-sonnet")
    
    @property
    def secret_key(self) -> Optional[str]:
        return self.get_value("SECRET_KEY")
    
    @property
    def database_host(self) -> Optional[str]:
        return self.get_value("DATABASE_HOST")
    
    @property
    def database_name(self) -> Optional[str]:
        return self.get_value("DATABASE_NAME")
    
    @property
    def database_user(self) -> Optional[str]:
        return self.get_value("DATABASE_USER")
    
    @property
    def database_password(self) -> Optional[str]:
        return self.get_value("DATABASE_PASSWORD")
    
    @property
    def google_client_id(self) -> Optional[str]:
        return self.get_value("GOOGLE_CLIENT_ID")
    
    @property
    def google_client_secret(self) -> Optional[str]:
        return self.get_value("GOOGLE_CLIENT_SECRET")
    
    @property
    def github_client_id(self) -> Optional[str]:
        return self.get_value("GITHUB_CLIENT_ID")
    
    @property
    def github_client_secret(self) -> Optional[str]:
        return self.get_value("GITHUB_CLIENT_SECRET")
    
    @property
    def ssl_cipher_suites(self) -> Optional[str]:
        return self.get_value("SSL_CIPHER_SUITES")
    
    @property
    def min_tls_version(self) -> Optional[str]:
        return self.get_value("MIN_TLS_VERSION")
    
    def get_database_url(self) -> Optional[str]:
        """Construct database URL from components"""
        host = self.database_host
        name = self.database_name
        user = self.database_user
        password = self.database_password
        port = os.getenv("DATABASE_PORT", "5432")
        
        if all([host, name, user, password]):
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"
        return None
    
    def get_database_url_async(self) -> Optional[str]:
        """Construct async database URL from components"""
        host = self.database_host
        name = self.database_name
        user = self.database_user
        password = self.database_password
        port = os.getenv("DATABASE_PORT", "5432")
        
        if all([host, name, user, password]):
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
        return None
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration values for debugging"""
        return {
            "environment": self.environment,
            "project_name": self.project_name,
            "is_cloud_deployment": self.is_cloud_deployment,
            "ssm_client_available": self.ssm_client is not None,
            "openrouter_api_key": "***" if self.openrouter_api_key else None,
            "openrouter_llm_model": self.openrouter_llm_model,
            "secret_key": "***" if self.secret_key else None,
            "database_host": self.database_host,
            "database_name": self.database_name,
            "database_user": self.database_user,
            "database_password": "***" if self.database_password else None,
            "google_client_id": self.google_client_id,
            "google_client_secret": "***" if self.google_client_secret else None,
            "github_client_id": self.github_client_id,
            "github_client_secret": "***" if self.github_client_secret else None,
            "ssl_cipher_suites": self.ssl_cipher_suites,
            "min_tls_version": self.min_tls_version,
        }

# Global configuration instance
@lru_cache()
def get_config() -> Config:
    """Get cached configuration instance"""
    return Config()

# Convenience functions for backward compatibility
def get_openrouter_api_key() -> Optional[str]:
    return get_config().openrouter_api_key

def get_openrouter_llm_model() -> Optional[str]:
    return get_config().openrouter_llm_model

def get_secret_key() -> Optional[str]:
    return get_config().secret_key

def get_database_url() -> Optional[str]:
    return get_config().get_database_url()

def get_database_url_async() -> Optional[str]:
    return get_config().get_database_url_async()
