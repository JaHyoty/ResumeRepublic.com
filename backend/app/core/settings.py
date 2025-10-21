"""
Simplified Settings Configuration
Uses unified configuration system for both local and cloud environments
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
import structlog
import secrets
from app.core.config import get_config

logger = structlog.get_logger(__name__)

class Settings(BaseSettings):
    """Simplified application settings using unified configuration"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database - will be constructed from unified config
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/resumerepublic"
    DATABASE_URL_ASYNC: str = "postgresql+asyncpg://user:password@localhost:5432/resumerepublic"
    
    # Database components (for ECS deployment)
    DATABASE_HOST: Optional[str] = None
    DATABASE_NAME: Optional[str] = None
    DATABASE_USER: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None
    DATABASE_PORT: int = 5432
    DATABASE_CREDENTIALS_SECRET_ARN: Optional[str] = None
    DATABASE_CREDENTIALS_CACHE_TTL: int = 300  # 5 minutes
    
    # S3 Configuration
    RESUMES_S3_BUCKET: Optional[str] = None
    RESUMES_CLOUDFRONT_DOMAIN: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    
    # CloudFront Signed URLs Configuration
    CLOUDFRONT_KEY_PAIR_ID: Optional[str] = None
    CLOUDFRONT_PRIVATE_KEY_PATH: Optional[str] = None
    
    # IAM Database Authentication
    USE_IAM_DATABASE_AUTH: bool = False
    
    # Database Connection Pool Settings
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 300
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    APPLE_CLIENT_ID: Optional[str] = None
    APPLE_CLIENT_SECRET: Optional[str] = None
    
    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://localhost:5173", 
        "http://localhost:4173",
        "https://dev.resumerepublic.com",
        "https://resumerepublic.com"
    ]
    ALLOWED_HOSTS: Union[List[str], str] = ["localhost", "127.0.0.1"]
    
    # External Services
    PARSING_SERVICE_URL: str = "http://localhost:8001"
    BACKEND_URL: str = "http://localhost:8000"
    
    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # LLM Configuration
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_LLM_MODEL: Optional[str] = None
    
    # SSL/TLS Configuration
    ENFORCE_TLS: bool = True
    SSL_VERIFY_CERTIFICATES: bool = True
    SSL_CIPHER_SUITES: str = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
    MIN_TLS_VERSION: str = "TLSv1.2"
    
    # Development SSL Configuration
    SSL_VERIFY_CERTIFICATES_DEV: bool = False
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse CORS origins from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        elif isinstance(v, list):
            return v
        else:
            return [str(v)]
    
    @field_validator('ALLOWED_HOSTS', mode='before')
    @classmethod
    def parse_cors_hosts(cls, v) -> List[str]:
        """Parse CORS hosts from string or list"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(',') if host.strip()]
        elif isinstance(v, list):
            return v
        else:
            return [str(v)]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Load values from configuration
        self._load_from_config()
        
        # Construct DATABASE_URL from components if available
        self._construct_database_urls()
        
        # Log configuration
        self._log_configuration()
        
        # Validate production settings
        if self.ENVIRONMENT == "production":
            self._validate_production_settings()
    
    def _load_from_config(self):
        """Load configuration values from config system"""
        # Don't load from config to avoid circular dependency
        # The config will handle the priority order
        pass
    
    def _construct_database_urls(self):
        """Construct database URLs from individual components"""
        if (self.DATABASE_HOST and self.DATABASE_NAME and 
            self.DATABASE_USER and self.DATABASE_PASSWORD):
            self.DATABASE_URL = f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
            self.DATABASE_URL_ASYNC = f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    def _log_configuration(self):
        """Log configuration for debugging"""
        config = get_config()
        config_info = config.get_all_config()
        
        logger.info("Configuration loaded", 
                   environment=self.ENVIRONMENT,
                   is_cloud_deployment=config_info["is_cloud_deployment"],
                   ssm_available=config_info["ssm_client_available"],
                   database_configured=bool(self.DATABASE_URL and self.DATABASE_URL != "postgresql://user:password@localhost:5432/resumerepublic"),
                   openrouter_configured=bool(self.OPENROUTER_API_KEY))
    
    def _validate_production_settings(self):
        """Validate required settings for production"""
        required_settings = ["SECRET_KEY", "DATABASE_URL"]
        
        missing_settings = []
        for setting in required_settings:
            value = getattr(self, setting)
            if not value or value in [
                "your-secret-key-change-in-production",
                "postgresql://user:password@localhost:5432/resumerepublic"
            ]:
                missing_settings.append(setting)
        
        if missing_settings:
            raise ValueError(
                f"Missing required settings for production: {', '.join(missing_settings)}"
            )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create settings instance
settings = Settings()
