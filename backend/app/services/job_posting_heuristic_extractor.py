"""
Job posting heuristic extractor
Extracts job data using DOM analysis and heuristics
"""

import re
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
import structlog

from app.services.job_posting_web_scraper import JobPostingWebScraper
from app.utils.job_posting_extractor_utils import JobPostingExtractorUtils

logger = structlog.get_logger()


class JobPostingHeuristicExtractor:
    """Extracts job posting data using DOM heuristics"""
    
    def __init__(self):
        self.web_scraper = JobPostingWebScraper()
    
    async def extract_job_data(self, url: str, html_content: str = None) -> Optional[Dict[str, Any]]:
        """
        Extract job data using heuristic DOM analysis
        """
        try:
            # Fetch HTML content if not provided
            if html_content is None:
                html_content = await self.web_scraper.fetch_html(url)
                if not html_content:
                    return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Use general heuristics
            return self._extract_with_heuristics(soup, url)
            
        except Exception as e:
            logger.error("Heuristic extraction failed", url=url, error=str(e))
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
            
            for i, element in enumerate(elements):
                text = element.get_text().strip()
                if self._is_valid_title(text):
                    return JobPostingExtractorUtils.clean_title(text)
        
        # Try meta tags
        meta_title = soup.find('meta', {'property': 'og:title'})
        if meta_title and meta_title.get('content'):
            title = meta_title['content'].strip()
            if self._is_valid_title(title):
                return JobPostingExtractorUtils.clean_title(title)
        
        return None
    
    def _extract_company_heuristic(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract company name using heuristics"""
        # PRIORITY 1: Try extracting company from page title (most accurate)
        title_company = JobPostingExtractorUtils.extract_company_from_title(soup, "Heuristic extractor")
        if title_company:
            logger.info(f"Company extracted from page title: '{title_company}'")
            return title_company
        
        # PRIORITY 2: Try meta tags (multiple sources)
        meta_sources = [
            {'property': 'og:site_name'},
            {'name': 'application-name'},
            {'name': 'apple-mobile-web-app-title'},
            {'property': 'og:title'},
            {'name': 'title'}
        ]
        
        for meta_attr in meta_sources:
            meta_company = soup.find('meta', meta_attr)
            if meta_company and meta_company.get('content'):
                company = meta_company['content'].strip()
                if JobPostingExtractorUtils.is_valid_company(company):
                    logger.info(f"Company extracted from meta tag {meta_attr}: '{company}'")
                    return JobPostingExtractorUtils.clean_company(company)
        
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
            
            for i, element in enumerate(elements):
                text = element.get_text().strip()
                if JobPostingExtractorUtils.is_valid_company(text):
                    return JobPostingExtractorUtils.clean_company(text)
        
        # Fallback to domain name
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        if domain:
            # Remove www. prefix
            company = domain.replace('www.', '').split('.')[0]
            if JobPostingExtractorUtils.is_valid_company(company):
                return JobPostingExtractorUtils.clean_company(company.title())
        
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
            '[class*="job-info"]',
            '[class*="job-desc"]',
            'article',
            '.content'
        ]
        
        best_description = None
        best_score = 0
        
        for selector in description_selectors:
            elements = soup.select(selector)
            
            for i, element in enumerate(elements):
                # Clean text while preserving paragraph structure
                cleaned_text = self._extract_and_clean_text([element])
                
                # Filter out navigation content from the cleaned text
                if self._contains_navigation_patterns(cleaned_text):
                    continue
                
                score = self._score_description(cleaned_text)
                is_valid = self._is_valid_description(cleaned_text)
                
                if score > best_score and is_valid:
                    best_description = cleaned_text
                    best_score = score
        
        # If no description found with specific selectors, try paragraphs as fallback
        if not best_description:
            paragraphs = soup.find_all('p')
            substantial_paragraphs = []
            
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 100:  # Look for substantial paragraphs
                    substantial_paragraphs.append(text)
            
            if substantial_paragraphs:
                # Combine substantial paragraphs
                combined_text = '\n\n'.join(substantial_paragraphs)
                cleaned_text = self._extract_and_clean_text([soup.new_string(combined_text)])
                
                # Check if this looks like a job description
                has_nav = self._contains_navigation_patterns(cleaned_text)
                is_valid = self._is_valid_description(cleaned_text)
                
                if not has_nav and is_valid:
                    best_description = cleaned_text
        
        return best_description
    
    def _filter_navigation_content(self, element) -> Optional[str]:
        """Filter out navigation and UI elements from job description content"""
        if not element:
            return None
        
        # Create a copy to avoid modifying the original
        from copy import deepcopy
        filtered_element = deepcopy(element)
        
        # Remove common navigation elements
        navigation_selectors = [
            'nav', 'header', 'footer', 'aside',
            '.nav', '.navigation', '.menu', '.breadcrumb',
            '.header', '.footer', '.sidebar',
            '.back-to', '.search-results', '.apply-button',
            '.job-actions', '.job-meta', '.job-location',
            'button', '.btn', '.button',
            'script', 'style', 'noscript'
        ]
        
        for selector in navigation_selectors:
            for nav_element in filtered_element.select(selector):
                nav_element.decompose()
        
        # Remove elements with navigation-related classes or IDs
        for elem in filtered_element.find_all():
            classes = elem.get('class', [])
            elem_id = elem.get('id', '')
            
            # Check for navigation-related class names
            nav_keywords = [
                'nav', 'menu', 'breadcrumb', 'header', 'footer',
                'sidebar', 'back', 'search', 'apply', 'button',
                'action', 'meta', 'location', 'breadcrumb'
            ]
            
            if any(keyword in ' '.join(classes).lower() for keyword in nav_keywords):
                elem.decompose()
            elif any(keyword in elem_id.lower() for keyword in nav_keywords):
                elem.decompose()
        
        # Get the remaining text
        remaining_text = filtered_element.get_text().strip()
        
        # Additional filtering based on content patterns
        if self._contains_navigation_patterns(remaining_text):
            return None
        
        return remaining_text
    
    def _contains_navigation_patterns(self, text: str) -> bool:
        """Check if text contains navigation patterns"""
        if not text:
            return True
        
        # Common navigation patterns
        nav_patterns = [
            'back to search results',
            'additional locations',
            'see less',
            'apply',
            'acknowledge',
            'refer a friend',
            'to proceed with your application',
            'you must be at least 18 years of age',
            'job id:',
            'multiple locations'
        ]
        
        text_lower = text.lower()
        
        # If more than 30% of the text matches navigation patterns, it's likely navigation
        nav_matches = sum(1 for pattern in nav_patterns if pattern in text_lower)
        if nav_matches > len(nav_patterns) * 0.3:
            return True
        
        # Check if the text is too short (likely navigation)
        if len(text.strip()) < 200:
            return True
        
        # Check if it contains mostly navigation elements
        nav_words = ['apply', 'back', 'search', 'results', 'acknowledge', 'refer']
        words = text_lower.split()
        nav_word_count = sum(1 for word in words if word in nav_words)
        
        if len(words) > 0 and nav_word_count / len(words) > 0.1:
            return True
        
        return False
    
    def _extract_and_clean_text(self, elements: List) -> str:
        """Extract and clean text from elements while preserving paragraph structure and formatting lists"""
        if not elements:
            return ""
        
        # Get the HTML content of the element before converting to text
        element = elements[0]
        html_content = str(element)
        
        # First, handle specific HTML elements to preserve structure
        # Convert </p> tags to double line breaks (paragraph breaks)
        html_content = re.sub(r'</p>', '\n\n', html_content, flags=re.IGNORECASE)
        
        # Convert <br> and <br/> tags to single line breaks
        html_content = re.sub(r'<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)
        
        # Handle list items - convert <li> to bullet points
        # First, handle unordered lists <ul> and <ol> - add spacing around them
        html_content = re.sub(r'<(ul|ol)[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'</(ul|ol)>', '\n', html_content, flags=re.IGNORECASE)
        
        # Convert <li> tags to bullet points with proper formatting
        html_content = re.sub(r'<li[^>]*>', '\n- ', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'</li>', '', html_content, flags=re.IGNORECASE)
        
        # Handle other block elements that should have line breaks
        block_elements = ['div', 'section', 'article', 'header', 'footer', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        for element_name in block_elements:
            # Add line break after opening tags
            html_content = re.sub(f'<{element_name}[^>]*>', f'\n', html_content, flags=re.IGNORECASE)
            # Add line break before closing tags
            html_content = re.sub(f'</{element_name}>', '\n', html_content, flags=re.IGNORECASE)
        
        # Remove all remaining HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode common HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' ',
            '&ndash;': '-',
            '&mdash;': '—',
            '&hellip;': '...',
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        # Clean whitespace while preserving paragraph structure
        # Replace multiple consecutive line breaks with double line breaks (paragraph breaks)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Replace multiple spaces/tabs with single space within lines
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove leading/trailing whitespace from each line
        lines = text.split('\n')
        cleaned_lines = []
        
        for i, line in enumerate(lines):
            cleaned_line = line.strip()
            if cleaned_line:  # Only keep non-empty lines
                cleaned_lines.append(cleaned_line)
            elif cleaned_lines and cleaned_lines[-1] != '':  # Keep one empty line between paragraphs
                # Check if the previous line is a list item (starts with -)
                # If so, don't add empty line to avoid blank rows between list items
                if not cleaned_lines[-1].startswith('- '):
                    cleaned_lines.append('')
        
        # Join lines back together
        text = '\n'.join(cleaned_lines)
        
        # Final cleanup - remove excessive leading/trailing whitespace
        text = text.strip()
        
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
    
    def _is_valid_description(self, description: str) -> bool:
        """Validate job description"""
        if not description or len(description) < 50:
            return False
        
        # Check for job-related keywords
        job_keywords = [
            'responsibilities', 'requirements', 'qualifications', 'experience',
            'skills', 'education', 'degree', 'years', 'salary', 'benefits',
            'location', 'remote', 'full-time', 'part-time', 'contract',
            'about', 'company', 'team', 'role', 'position', 'engineer',
            'developer', 'analyst', 'manager', 'specialist', 'coordinator'
        ]
        
        description_lower = description.lower()
        keyword_count = sum(1 for keyword in job_keywords if keyword in description_lower)
        
        # Be more flexible - require at least 1 keyword instead of 2
        return keyword_count >= 1
    
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
