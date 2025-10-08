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
    
    async def fetch_with_rendering(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and render page with JavaScript execution
        Returns dict with HTML and metadata
        """
        # For now, return basic fetch
        # In production, this would use Playwright or similar
        html = await self.fetch_html(url)
        if not html:
            return None
        
        return {
            'html': html,
            'url': url,
            'rendered': False,  # Would be True with Playwright
            'metadata': {
                'fetch_time': time.time(),
                'method': 'httpx'
            }
        }
    
    def sanitize_html(self, html: str, max_size: int = 500000) -> str:
        """
        Sanitize HTML for storage and processing
        Remove scripts, forms, and limit size
        """
        import re
        
        # Remove script tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove style tags
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove form elements
        html = re.sub(r'<form[^>]*>.*?</form>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<input[^>]*>', '', html, flags=re.IGNORECASE)
        
        # Remove comments
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        
        # Limit size
        if len(html) > max_size:
            html = html[:max_size] + "..."
        
        return html
