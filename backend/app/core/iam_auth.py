"""
IAM Database Authentication for AWS RDS
"""

import boto3
import structlog
from typing import Optional
from functools import lru_cache
from datetime import datetime, timedelta

logger = structlog.get_logger()


class IAMDatabaseAuth:
    """Handles IAM database authentication for AWS RDS"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self._rds_client = None
        self._token_cache = {}
        self._token_expiry = {}
    
    @property
    def rds_client(self):
        """Lazy initialization of RDS client"""
        if self._rds_client is None:
            self._rds_client = boto3.client('rds', region_name=self.region)
        return self._rds_client
    
    def generate_db_auth_token(
        self, 
        db_hostname: str, 
        port: int, 
        db_username: str
    ) -> str:
        """
        Generate IAM database authentication token
        
        Args:
            db_hostname: RDS endpoint hostname
            port: Database port
            db_username: Database username
            
        Returns:
            IAM authentication token
        """
        cache_key = f"{db_hostname}:{port}:{db_username}"
        now = datetime.utcnow()
        
        # Check if we have a valid cached token
        if (cache_key in self._token_cache and 
            cache_key in self._token_expiry and 
            now < self._token_expiry[cache_key]):
            logger.debug("Using cached IAM database token", cache_key=cache_key)
            return self._token_cache[cache_key]
        
        try:
            logger.info("Generating new IAM database token", 
                       hostname=db_hostname, port=port, username=db_username)
            
            # Generate the token
            token = self.rds_client.generate_db_auth_token(
                DBHostname=db_hostname,
                Port=port,
                DBUsername=db_username
            )
            
            # Cache the token (valid for 15 minutes, cache for 14 minutes)
            self._token_cache[cache_key] = token
            self._token_expiry[cache_key] = now + timedelta(minutes=14)
            
            logger.info("IAM database token generated successfully")
            return token
            
        except Exception as e:
            logger.error("Failed to generate IAM database token", 
                        error=str(e), hostname=db_hostname, port=port, username=db_username)
            raise
    
    def get_connection_params(
        self, 
        db_hostname: str, 
        port: int, 
        db_name: str, 
        db_username: str
    ) -> dict:
        """
        Get database connection parameters for IAM authentication
        
        Args:
            db_hostname: RDS endpoint hostname
            port: Database port
            db_name: Database name
            db_username: Database username
            
        Returns:
            Dictionary with connection parameters
        """
        token = self.generate_db_auth_token(db_hostname, port, db_username)
        
        return {
            'host': db_hostname,
            'port': port,
            'database': db_name,
            'user': db_username,
            'password': token,  # IAM token as password
            'sslmode': 'require'
        }


# Global instance
iam_auth = IAMDatabaseAuth()


def get_iam_db_connection_params(
    db_hostname: str, 
    port: int, 
    db_name: str, 
    db_username: str
) -> dict:
    """
    Convenience function to get IAM database connection parameters
    
    Args:
        db_hostname: RDS endpoint hostname
        port: Database port
        db_name: Database name
        db_username: Database username
        
    Returns:
        Dictionary with connection parameters
    """
    return iam_auth.get_connection_params(db_hostname, port, db_name, db_username)
