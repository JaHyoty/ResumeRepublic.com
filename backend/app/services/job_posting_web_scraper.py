"""
Job posting web scraper
Handles fetching and rendering of web pages for job posting extraction
"""

import asyncio
import time
from typing import Optional, Dict, Any
import httpx
import structlog
from urllib.parse import urlparse

logger = structlog.get_logger()


class JobPostingWebScraper:
    """Web scraper for job posting pages"""
    
    def __init__(self):
        self.timeout = 30
        self.max_retries = 3
        self.user_agent = "Mozilla/5.0 (compatible; JobPostingBot/1.0; +https://resumerepublic.com/bot)"
    
    async def fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from URL
        Returns raw HTML or None if failed
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers={'User-Agent': self.user_agent},
                follow_redirects=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    logger.warning("Non-HTML content type", url=url, content_type=content_type)
                    return None
                
                return response.text
                
        except Exception as e:
            logger.error("Failed to fetch HTML", url=url, error=str(e))
            return None
    
