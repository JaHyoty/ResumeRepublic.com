"""
Configuration settings for CareerPathPro Backend
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
import structlog
import secrets
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database - REQUIRED in production
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/careerpathpro"
    DATABASE_URL_ASYNC: str = "postgresql+asyncpg://user:password@localhost:5432/careerpathpro"
    
    # Database components (for ECS deployment)
    DATABASE_HOST: Optional[str] = None
    DATABASE_NAME: Optional[str] = None
    DATABASE_USER: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None
    DATABASE_CREDENTIALS_SECRET_ARN: Optional[str] = None
    
    # IAM Database Authentication
    USE_IAM_DATABASE_AUTH: bool = False
    DATABASE_PORT: int = 5432
    
    # Security - REQUIRED in production
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Generate random key if not provided
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # OAuth - Optional, will be None if not provided
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    APPLE_CLIENT_ID: Optional[str] = None
    APPLE_CLIENT_SECRET: Optional[str] = None
    
    # CORS - Configurable via environment
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173", "http://localhost:4173"]
    ALLOWED_HOSTS: Union[List[str], str] = ["localhost", "127.0.0.1"]
    
    # External Services
    PARSING_SERVICE_URL: str = "http://localhost:8001"
    BACKEND_URL: str = "http://localhost:8000"
    
    # AWS - Optional, will be None if not provided
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    
    # Redis (for caching)
    REDIS_URL: str = "redis://localhost:6379"
    
    # LLM Configuration - Optional
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_LLM_MODEL: Optional[str] = None
    
    # SSL/TLS Configuration for External API Calls
    ENFORCE_TLS: bool = True
    SSL_VERIFY_CERTIFICATES: bool = True
    SSL_CIPHER_SUITES: str = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
    MIN_TLS_VERSION: str = "TLSv1.2"
    
    # Development SSL Configuration (WARNING: Only for development!)
    SSL_VERIFY_CERTIFICATES_DEV: bool = False  # Set to False for development environments with cert issues
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse CORS origins from comma-separated string or list"""
        logger = structlog.get_logger()
        
        logger.debug("Parsing ALLOWED_ORIGINS", input_value=v, input_type=type(v).__name__)
        
        if isinstance(v, str):
            # Handle comma-separated format: item1,item2
            result = [origin.strip() for origin in v.split(',') if origin.strip()]
            logger.debug("Parsed as comma-separated", result=result)
            return result
        elif isinstance(v, list):
            logger.debug("Already a list", result=v)
            return v
        else:
            # Fallback for other types
            result = [str(v)]
            logger.debug("Fallback parsing", result=result)
            return result
    
    @field_validator('ALLOWED_HOSTS', mode='before')
    @classmethod
    def parse_cors_hosts(cls, v) -> List[str]:
        """Parse CORS hosts from string or list"""
        logger = structlog.get_logger()
        
        logger.debug("Parsing ALLOWED_HOSTS", input_value=v, input_type=type(v).__name__)
        
        if isinstance(v, str):
            # Handle comma-separated format: item1,item2
            result = [host.strip() for host in v.split(',') if host.strip()]
            logger.debug("Parsed as comma-separated", result=result)
            return result
        elif isinstance(v, list):
            logger.debug("Already a list", result=v)
            return v
        else:
            # Fallback for other types
            result = [str(v)]
            logger.debug("Fallback parsing", result=result)
            return result
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Construct DATABASE_URL from individual components if provided
        if (self.DATABASE_HOST and self.DATABASE_NAME and 
            self.DATABASE_USER and self.DATABASE_PASSWORD):
            self.DATABASE_URL = f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
            self.DATABASE_URL_ASYNC = f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        
        # Log configuration values for debugging
        logger = structlog.get_logger()
        
        logger.info("Configuration loaded", 
                   allowed_origins=self.ALLOWED_ORIGINS,
                   allowed_hosts=self.ALLOWED_HOSTS,
                   environment=self.ENVIRONMENT,
                   database_url_configured=bool(self.DATABASE_URL and self.DATABASE_URL != "postgresql://user:password@localhost:5432/careerpathpro"))
        
        # Validate required settings for production
        if self.ENVIRONMENT == "production":
            self._validate_production_settings()
    
    def _validate_production_settings(self):
        """Validate that required settings are provided in production"""
        required_settings = [
            "SECRET_KEY",
            "DATABASE_URL",
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not getattr(self, setting) or getattr(self, setting) in [
                "your-secret-key-change-in-production",
                "postgresql://user:password@localhost:5432/careerpathpro"
            ]:
                missing_settings.append(setting)
        
        if missing_settings:
            raise ValueError(
                f"Missing required environment variables for production: {', '.join(missing_settings)}"
            )
    
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()
