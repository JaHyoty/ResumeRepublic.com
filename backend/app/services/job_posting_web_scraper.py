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
        self.timeout = 8
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
                # Launch browser with stealth settings to avoid bot detection
                # Add more robust arguments for containerized environments
                browser_args = [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',  # Additional sandbox bypass for containers
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # Speed up loading
                    '--disable-javascript-harmony-shipping',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-gpu',  # Disable GPU in headless mode
                    '--disable-software-rasterizer',
                    '--disable-background-networking',
                    '--disable-default-apps',
                    '--disable-sync',
                    '--disable-translate',
                    '--hide-scrollbars',
                    '--metrics-recording-only',
                    '--mute-audio',
                    '--no-first-run',
                    '--safebrowsing-disable-auto-update',
                    '--disable-ipc-flooding-protection',
                    '--disable-hang-monitor',
                    '--disable-prompt-on-repost',
                    '--disable-domain-reliability',
                    '--disable-client-side-phishing-detection',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-features=TranslateUI',
                    '--disable-features=BlinkGenPropertyTrees',
                    '--run-all-compositor-stages-before-draw',
                    '--disable-threaded-animation',
                    '--disable-threaded-scrolling',
                    '--disable-checker-imaging',
                    '--disable-new-content-rendering-timeout',
                    '--disable-image-animation-resync',
                    '--disable-partial-raster',
                    '--disable-skia-runtime-opts',
                    '--disable-system-font-check',
                    '--disable-font-subpixel-positioning'
                ]
                
                browser = await p.chromium.launch(
                    headless=True,
                    args=browser_args
                )
                
                # Create context with realistic settings
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='America/New_York',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                
                page = await context.new_page()
                
                # Remove webdriver property to avoid detection
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                
                # Navigate to the page with efficient loading strategy
                try:
                    # First, wait for network to be idle
                    await page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)
                    
                    # Then wait specifically for JSON-LD to appear (if it loads dynamically)
                    try:
                        await page.wait_for_function("""
                            () => document.querySelectorAll('script[type="application/ld+json"]').length > 0
                        """, timeout=self.timeout * 1000)
                    except Exception:
                        pass  # JSON-LD not found dynamically, continue with current content
                        
                except Exception as nav_error:
                    logger.warning("DOM content loaded timeout, trying load", url=url, error=str(nav_error))
                    await page.goto(url, wait_until='load', timeout=self.timeout * 1000)
                
                
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