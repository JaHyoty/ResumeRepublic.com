"""
Google OAuth verification service
"""

from typing import Optional, Dict, Any
from google.auth.transport import requests
from google.oauth2 import id_token
from google.auth.exceptions import GoogleAuthError
import structlog

from app.core.settings import settings

logger = structlog.get_logger()


class GoogleOAuthService:
    """Service for handling Google OAuth verification"""
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
    
    async def verify_id_token(self, id_token_str: str) -> Optional[Dict[str, Any]]:
        """
        Verify Google ID token and return user information
        
        Args:
            id_token_str: The ID token from Google
            
        Returns:
            Dict containing user information if valid, None if invalid
        """
        try:
            if not self.client_id:
                logger.error("Google OAuth not configured - missing GOOGLE_CLIENT_ID")
                return None
            
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                id_token_str, 
                requests.Request(), 
                self.client_id
            )
            
            # Verify the issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                logger.warning("Invalid token issuer", issuer=idinfo.get('iss'))
                return None
            
            # Extract user information
            user_info = {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'email_verified': idinfo.get('email_verified', False),
                'name': idinfo.get('name', ''),
                'given_name': idinfo.get('given_name', ''),
                'family_name': idinfo.get('family_name', ''),
                'picture': idinfo.get('picture', ''),
            }
            
            logger.info("Google OAuth token verified successfully", 
                       email=user_info['email'], 
                       google_id=user_info['google_id'])
            
            return user_info
            
        except GoogleAuthError as e:
            logger.error("Google OAuth verification failed", error=str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error during Google OAuth verification", error=str(e))
            return None


# Create singleton instance
google_oauth_service = GoogleOAuthService()
