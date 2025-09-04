"""
Configuration settings for CareerPathPro Parsing Service
"""

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # External Services
    BACKEND_URL: str = "http://localhost:8000"
    
    # LLM Configuration - At least one API key is required
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "openai"
    
    # File Processing
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".docx", ".doc"]
    TEMP_DIR: str = "/tmp/careerpathpro"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Storage - Optional
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate LLM configuration
        self._validate_llm_settings()
    
    def _validate_llm_settings(self):
        """Validate that at least one LLM provider is configured"""
        if not self.OPENAI_API_KEY and not self.ANTHROPIC_API_KEY:
            raise ValueError(
                "At least one LLM API key must be provided: OPENAI_API_KEY or ANTHROPIC_API_KEY"
            )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
