"""
Job posting heuristic extractor
Extracts job data using DOM analysis and heuristics
"""

import re
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
import structlog

from app.services.job_posting_web_scraper import JobPostingWebScraper

logger = structlog.get_logger()


class JobPostingHeuristicExtractor:
    """Extracts job posting data using DOM heuristics"""
    
    def __init__(self):
        self.web_scraper = JobPostingWebScraper()
    
    async def extract_job_data(self, url: str, domain_selectors: Optional[List[Dict]] = None) -> Optional[Dict[str, Any]]:
        """
        Extract job data using heuristic DOM analysis
        """
        try:
            # Fetch HTML content
            html_content = await self.web_scraper.fetch_html(url)
            if not html_content:
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try domain-specific selectors first
            if domain_selectors:
                result = self._extract_with_domain_selectors(soup, domain_selectors)
                if result:
                    return result
            
            # Fall back to general heuristics
            return self._extract_with_heuristics(soup, url)
            
        except Exception as e:
            logger.error("Heuristic extraction failed", url=url, error=str(e))
            return None
    
    def _extract_with_domain_selectors(self, soup: BeautifulSoup, selectors: List[Dict]) -> Optional[Dict[str, Any]]:
        """Extract using domain-specific selectors"""
        try:
            result = {}
            
            for selector_info in selectors:
                field = selector_info.get('field')
                selector = selector_info.get('selector')
                selector_type = selector_info.get('type', 'css')
                
                if not field or not selector:
                    continue
                
                # Apply selector
                elements = self._apply_selector(soup, selector, selector_type)
                if elements:
                    text = self._extract_text_from_elements(elements)
                    if text and len(text.strip()) > 2:
                        result[field] = text.strip()
            
            # Validate result
            if self._is_valid_heuristic_result(result):
                return {
                    **result,
                    'confidence': 0.8,
                    'excerpt': result.get('description', '')[:200] + '...' if result.get('description') else '',
                    'provenance': {
                        'method': 'heuristic',
                        'extractor': 'domain_selectors',
                        'source': 'cached_selectors'
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error("Domain selector extraction failed", error=str(e))
            return None
    
    def _extract_with_heuristics(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """Extract using general heuristics"""
        try:
            result = {}
            
            # Extract title
            title = self._extract_title_heuristic(soup)
            if title:
                result['title'] = title
            
            # Extract company
            company = self._extract_company_heuristic(soup, url)
            if company:
                result['company'] = company
            
            # Extract description
            description = self._extract_description_heuristic(soup)
            if description:
                result['description'] = description
            
            # Validate result
            if self._is_valid_heuristic_result(result):
                return {
                    **result,
                    'confidence': 0.6,
                    'excerpt': result.get('description', '')[:200] + '...' if result.get('description') else '',
                    'provenance': {
                        'method': 'heuristic',
                        'extractor': 'general_heuristics',
                        'source': 'dom_analysis'
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error("General heuristic extraction failed", error=str(e))
            return None
    
    def _extract_title_heuristic(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job title using heuristics"""
        # Try common title selectors
        title_selectors = [
            'h1',
            'h2',
            '.job-title',
            '.position-title',
            '[class*="title"]',
            '[class*="position"]',
            '[class*="role"]'
        ]
        
        for selector in title_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if self._is_valid_title(text):
                    return text
        
        # Try meta tags
        meta_title = soup.find('meta', {'property': 'og:title'})
        if meta_title and meta_title.get('content'):
            title = meta_title['content'].strip()
            if self._is_valid_title(title):
                return title
        
        return None
    
    def _extract_company_heuristic(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract company name using heuristics"""
        # Try meta tags first
        meta_company = soup.find('meta', {'property': 'og:site_name'})
        if meta_company and meta_company.get('content'):
            company = meta_company['content'].strip()
            if self._is_valid_company(company):
                return company
        
        # Try common company selectors
        company_selectors = [
            '.company-name',
            '.employer',
            '[class*="company"]',
            '[class*="employer"]',
            '.organization'
        ]
        
        for selector in company_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if self._is_valid_company(text):
                    return text
        
        # Fallback to domain name
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        if domain:
            # Remove www. prefix
            company = domain.replace('www.', '').split('.')[0]
            if self._is_valid_company(company):
                return company.title()
        
        return None
    
    def _extract_description_heuristic(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job description using heuristics"""
        # Try common description selectors
        description_selectors = [
            '.job-description',
            '.description',
            '.job-details',
            '.requirements',
            '.responsibilities',
            '[class*="description"]',
            '[class*="details"]',
            'article',
            '.content'
        ]
        
        best_description = None
        best_score = 0
        
        for selector in description_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                score = self._score_description(text)
                
                if score > best_score and self._is_valid_description(text):
                    best_description = text
                    best_score = score
        
        return best_description
    
    def _apply_selector(self, soup: BeautifulSoup, selector: str, selector_type: str) -> List:
        """Apply CSS or XPath selector to soup"""
        if selector_type == 'css':
            return soup.select(selector)
        elif selector_type == 'xpath':
            # For XPath, we'd need lxml
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
    
    def _is_valid_title(self, title: str) -> bool:
        """Validate job title"""
        if not title or len(title) < 3:
            return False
        
        # Check for common job title keywords
        job_keywords = [
            'engineer', 'developer', 'manager', 'analyst', 'specialist',
            'coordinator', 'director', 'lead', 'senior', 'junior',
            'intern', 'consultant', 'architect', 'designer', 'programmer'
        ]
        
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in job_keywords) or len(title) > 10
    
    def _is_valid_company(self, company: str) -> bool:
        """Validate company name"""
        if not company or len(company) < 2:
            return False
        
        # Avoid generic terms
        generic_terms = ['home', 'page', 'website', 'site', 'www', 'http']
        company_lower = company.lower()
        
        return not any(term in company_lower for term in generic_terms)
    
    def _is_valid_description(self, description: str) -> bool:
        """Validate job description"""
        if not description or len(description) < 50:
            return False
        
        # Check for job-related keywords
        job_keywords = [
            'responsibilities', 'requirements', 'qualifications', 'experience',
            'skills', 'education', 'degree', 'years', 'salary', 'benefits',
            'location', 'remote', 'full-time', 'part-time', 'contract'
        ]
        
        description_lower = description.lower()
        keyword_count = sum(1 for keyword in job_keywords if keyword in description_lower)
        
        return keyword_count >= 2
    
    def _score_description(self, text: str) -> float:
        """Score description text for relevance"""
        if not text:
            return 0.0
        
        score = 0.0
        
        # Length score
        if len(text) > 200:
            score += 0.3
        elif len(text) > 100:
            score += 0.2
        
        # Keyword score
        job_keywords = [
            'responsibilities', 'requirements', 'qualifications', 'experience',
            'skills', 'education', 'degree', 'years', 'salary', 'benefits'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in job_keywords if keyword in text_lower)
        score += min(keyword_count * 0.1, 0.4)
        
        # Structure score (check for lists, paragraphs)
        if '<ul>' in text or '<ol>' in text:
            score += 0.1
        if '<p>' in text:
            score += 0.1
        
        return min(score, 1.0)
    
    def _is_valid_heuristic_result(self, result: Dict[str, Any]) -> bool:
        """Validate heuristic extraction result"""
        title = result.get('title', '').strip()
        description = result.get('description', '').strip()
        
        # Must have title and description
        if not title or not description:
            return False
        
        # Title must be valid
        if not self._is_valid_title(title):
            return False
        
        # Description must be substantial
        if not self._is_valid_description(description):
            return False
        
        return True
