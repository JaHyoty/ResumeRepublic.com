"""
Job posting web scraper
Handles fetching and rendering of web pages for job posting extraction
Supports both basic HTTP requests and JavaScript rendering with Playwright
"""

import asyncio
import time
from typing import Optional, Dict, Any
import httpx
import structlog
from urllib.parse import urlparse
from playwright.async_api import async_playwright

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
        First tries basic HTTP request, then falls back to Playwright for JavaScript sites
        """
        # First try basic HTTP request
        html_content = await self._fetch_with_httpx(url)
        
        if html_content and self._has_substantial_content(html_content):
            logger.info("Successfully fetched content with HTTP", url=url)
            return html_content
        
        # If basic request failed or returned minimal content, try Playwright
        logger.info("Basic HTTP request failed or returned minimal content, trying Playwright", url=url)
        return await self._fetch_with_playwright(url)
    
    async def _fetch_with_httpx(self, url: str) -> Optional[str]:
        """Fetch HTML using basic HTTP request"""
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
            logger.error("Failed to fetch HTML with httpx", url=url, error=str(e))
            return None
    
    async def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """Fetch HTML using Playwright for JavaScript-heavy sites"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set user agent
                await page.set_extra_http_headers({'User-Agent': self.user_agent})
                
                # Navigate to the page
                await page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)
                
                # Wait a bit for any additional content to load
                await page.wait_for_timeout(2000)
                
                # Get the HTML content
                html_content = await page.content()
                
                await browser.close()
                
                logger.info("Successfully fetched content with Playwright", url=url)
                return html_content
                
        except Exception as e:
            logger.error("Failed to fetch HTML with Playwright", url=url, error=str(e))
            return None
    
    def _has_substantial_content(self, html_content: str) -> bool:
        """
        Check if HTML content has substantial job-related content
        Returns True if content looks complete, False if it's likely a shell page
        """
        if not html_content:
            return False
        
        # Check for common job posting indicators
        job_indicators = [
            'job description', 'job requirements', 'qualifications',
            'responsibilities', 'salary', 'benefits', 'apply now',
            'job title', 'company', 'location', 'experience'
        ]
        
        html_lower = html_content.lower()
        found_indicators = sum(1 for indicator in job_indicators if indicator in html_lower)
        
        # If we found at least 3 job-related indicators, consider it substantial
        return found_indicators >= 3