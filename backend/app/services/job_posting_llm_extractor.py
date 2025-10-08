"""
Job posting LLM extractor
Uses LLM to discover selectors and extract job data
"""

import json
import re
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
import structlog

from app.services.job_posting_web_scraper import JobPostingWebScraper
from app.services.llm_service import LLMService

logger = structlog.get_logger()


class JobPostingLLMExtractor:
    """Extracts job posting data using LLM assistance"""
    
    def __init__(self):
        self.web_scraper = JobPostingWebScraper()
        self.llm_service = LLMService()
    
    async def extract_job_data(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract job data using LLM-assisted selector discovery
        """
        try:
            # Fetch and render page
            page_data = await self.web_scraper.fetch_with_rendering(url)
            if not page_data or not page_data.get('html'):
                return None
            
            html_content = page_data['html']
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Sanitize HTML for LLM processing
            sanitized_html = self._sanitize_for_llm(html_content)
            
            # Use LLM to discover selectors
            selectors = await self._discover_selectors_with_llm(sanitized_html)
            if not selectors:
                return None
            
            # Apply discovered selectors
            result = self._apply_llm_selectors(soup, selectors)
            if result and self._is_valid_llm_result(result):
                return {
                    **result,
                    'confidence': 0.7,
                    'excerpt': result.get('description', '')[:200] + '...' if result.get('description') else '',
                    'provenance': {
                        'method': 'llm',
                        'extractor': 'llm_selector_discovery',
                        'source': 'ai_assisted',
                        'selectors': selectors
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error("LLM extraction failed", url=url, error=str(e))
            return None
    
    def _sanitize_for_llm(self, html: str) -> str:
        """Sanitize HTML for LLM processing"""
        # Remove scripts, styles, and forms
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<form[^>]*>.*?</form>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove comments
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        
        # Limit size to avoid token limits
        if len(html) > 50000:
            html = html[:50000] + "..."
        
        return html
    
    async def _discover_selectors_with_llm(self, html: str) -> Optional[List[Dict[str, Any]]]:
        """Use LLM to discover CSS selectors for job data"""
        try:
            prompt = self._build_selector_discovery_prompt(html)
            
            response = await self.llm_service.generate_completion(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.1
            )
            
            if not response:
                return None
            
            # Parse LLM response
            selectors = self._parse_llm_selector_response(response)
            return selectors
            
        except Exception as e:
            logger.error("LLM selector discovery failed", error=str(e))
            return None
    
    def _build_selector_discovery_prompt(self, html: str) -> str:
        """Build prompt for LLM selector discovery"""
        return f"""
You are a web scraping expert. Analyze the following HTML and provide CSS selectors to extract job posting information.

HTML Content:
{html[:10000]}...

Please return a JSON array with selectors for:
1. Job title (field: "title")
2. Company name (field: "company") 
3. Job description (field: "description")

For each selector, provide:
- type: "css" or "xpath"
- selector: the actual CSS selector or XPath
- field: "title", "company", or "description"
- confidence: 0.0 to 1.0

Example response:
[
  {{
    "type": "css",
    "selector": "h1.job-title",
    "field": "title",
    "confidence": 0.9
  }},
  {{
    "type": "css", 
    "selector": ".company-name",
    "field": "company",
    "confidence": 0.8
  }},
  {{
    "type": "css",
    "selector": ".job-description",
    "field": "description", 
    "confidence": 0.9
  }}
]

Return only the JSON array, no other text.
"""
    
    def _parse_llm_selector_response(self, response: str) -> Optional[List[Dict[str, Any]]]:
        """Parse LLM response to extract selectors"""
        try:
            # Clean response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            
            response = response.strip()
            
            # Parse JSON
            selectors = json.loads(response)
            
            if not isinstance(selectors, list):
                return None
            
            # Validate selectors
            valid_selectors = []
            for selector in selectors:
                if self._is_valid_selector(selector):
                    valid_selectors.append(selector)
            
            return valid_selectors if valid_selectors else None
            
        except Exception as e:
            logger.error("Failed to parse LLM selector response", error=str(e))
            return None
    
    def _is_valid_selector(self, selector: Dict[str, Any]) -> bool:
        """Validate selector object"""
        required_fields = ['type', 'selector', 'field', 'confidence']
        
        if not all(field in selector for field in required_fields):
            return False
        
        if selector['type'] not in ['css', 'xpath']:
            return False
        
        if selector['field'] not in ['title', 'company', 'description']:
            return False
        
        if not isinstance(selector['confidence'], (int, float)):
            return False
        
        if not 0.0 <= selector['confidence'] <= 1.0:
            return False
        
        if not selector['selector'] or not selector['selector'].strip():
            return False
        
        return True
    
    def _apply_llm_selectors(self, soup: BeautifulSoup, selectors: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Apply LLM-discovered selectors to extract data"""
        try:
            result = {}
            
            for selector_info in selectors:
                field = selector_info['field']
                selector = selector_info['selector']
                selector_type = selector_info['type']
                
                # Apply selector
                elements = self._apply_selector(soup, selector, selector_type)
                if elements:
                    text = self._extract_text_from_elements(elements)
                    if text and len(text.strip()) > 2:
                        result[field] = text.strip()
            
            return result if result else None
            
        except Exception as e:
            logger.error("Failed to apply LLM selectors", error=str(e))
            return None
    
    def _apply_selector(self, soup: BeautifulSoup, selector: str, selector_type: str) -> List:
        """Apply CSS or XPath selector"""
        if selector_type == 'css':
            try:
                return soup.select(selector)
            except Exception:
                return []
        elif selector_type == 'xpath':
            # XPath support would require lxml
            # For now, return empty list
            return []
        else:
            return []
    
    def _extract_text_from_elements(self, elements: List) -> str:
        """Extract and clean text from elements"""
        if not elements:
            return ""
        
        # Get text from first element
        text = elements[0].get_text()
        
        # Clean up text
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _is_valid_llm_result(self, result: Dict[str, Any]) -> bool:
        """Validate LLM extraction result"""
        title = result.get('title', '').strip()
        description = result.get('description', '').strip()
        
        # Must have title and description
        if not title or not description:
            return False
        
        # Title must be reasonable length
        if len(title) < 3 or len(title) > 200:
            return False
        
        # Description must be substantial
        if len(description) < 50:
            return False
        
        return True
