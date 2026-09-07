"""
Simplified Settings Configuration — DynamoDB serverless version.
Removes PostgreSQL settings, adds DynamoDB table name.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
import structlog
import secrets

logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    """Application settings for serverless deployment"""

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # DynamoDB
    DYNAMODB_TABLE_NAME: str = "resumerepublic-production"

    # S3 Configuration
    RESUMES_S3_BUCKET: Optional[str] = None
    RESUMES_CLOUDFRONT_DOMAIN: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    # Worker Lambda Function Names (for async dispatch)
    PDF_LAMBDA_NAME: Optional[str] = None
    SCRAPER_LAMBDA_NAME: Optional[str] = None

    # CloudFront Signed URLs Configuration
    CLOUDFRONT_KEY_PAIR_ID: Optional[str] = None
    CLOUDFRONT_PRIVATE_KEY_PATH: Optional[str] = None

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cookie Configuration
    COOKIE_DOMAIN: Optional[str] = None
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

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
        "https://resumerepublic.com",
    ]
    ALLOWED_HOSTS: Union[List[str], str] = ["localhost", "127.0.0.1"]

    # External Services
    PARSING_SERVICE_URL: str = "http://localhost:8001"
    BACKEND_URL: str = "http://localhost:8000"

    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None

    # Redis (kept for future use)
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

        # Log configuration
        logger.info(
            "Configuration loaded",
            environment=self.ENVIRONMENT,
            dynamodb_table=self.DYNAMODB_TABLE_NAME,
            aws_region=self.AWS_REGION,
            openrouter_configured=bool(self.OPENROUTER_API_KEY),
        )

        # Validate production settings
        if self.ENVIRONMENT == "production":
            self._validate_production_settings()

    def _validate_production_settings(self):
        """Validate required settings for production"""
        if self.SECRET_KEY in ["your-secret-key-change-in-production", ""]:
            raise ValueError("SECRET_KEY must be set for production")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# Create settings instance
settings = Settings()
