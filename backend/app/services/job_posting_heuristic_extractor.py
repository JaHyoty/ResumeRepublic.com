"""
Job posting heuristic extractor
Extracts job data using DOM analysis and heuristics
"""

import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
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
            
            # Extract title and company together (more efficient and consistent)
            title, company = self._extract_title_and_company_heuristic(soup, url)
            if title:
                result['title'] = title
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
    
    def _extract_title_and_company_heuristic(self, soup: BeautifulSoup, url: str) -> tuple[Optional[str], Optional[str]]:
        """Extract job title and company using heuristics, returning (title, company) tuple"""
        title = None
        company = None
        
        # PRIORITY 1: Try extracting both from page title using combined utility method (most accurate)
        title, company = JobPostingExtractorUtils.extract_title_and_company_from_page_title(soup, "Heuristic extractor")
        
        # PRIORITY 2: Try meta tags for title if not found yet
        if not title:
            meta_tags = [
                {'property': 'og:title'},
                {'name': 'title'},
                {'name': 'twitter:title'}
            ]
            
            for meta_attr in meta_tags:
                meta_element = soup.find('meta', meta_attr)
                if meta_element and meta_element.get('content'):
                    title_text = meta_element['content'].strip()
                    extracted_title = JobPostingExtractorUtils._extract_title_from_page_title(title_text)
                    if extracted_title:
                        title = extracted_title
                        break
        
        # PRIORITY 3: Try meta tags for company if not found yet
        if not company:
            company_meta_tags = [
                {'property': 'og:site_name'},
                {'name': 'application-name'},
                {'name': 'apple-mobile-web-app-title'}
            ]
            
            for meta_attr in company_meta_tags:
                meta_element = soup.find('meta', meta_attr)
                if meta_element and meta_element.get('content'):
                    company_name = meta_element['content'].strip()
                    if JobPostingExtractorUtils.is_valid_company(company_name):
                        company = JobPostingExtractorUtils.clean_company(company_name)
                        break
        
        # PRIORITY 4: Try DOM selectors for title if not found yet
        if not title:
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
                    # Skip generic titles like "job details", "careers", etc.
                    if text.lower() in ['job details', 'careers', 'jobs', 'search results', 'more about us']:
                        continue
                        
                    if JobPostingExtractorUtils._is_valid_title(text) and len(text) > 10:
                        title = JobPostingExtractorUtils.clean_title(text)
                        break
                
                if title:
                    break
        
        # PRIORITY 5: Try DOM selectors for company if not found yet
        if not company:
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
                    if JobPostingExtractorUtils.is_valid_company(text):
                        company = JobPostingExtractorUtils.clean_company(text)
                        break
                
                if company:
                    break
        
        # PRIORITY 6: Fallback to URL-based company extraction if still not found
        if not company:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Extract company from domain
            domain_parts = domain.replace('www.', '').split('.')
            if len(domain_parts) >= 2:
                potential_company = domain_parts[0]
                if JobPostingExtractorUtils.is_valid_company(potential_company):
                    company = JobPostingExtractorUtils.clean_company(potential_company)
        
        return title, company
    
    
    
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
            '.content',
            'main',
            '[role="main"]'
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
                is_valid = JobPostingExtractorUtils.is_valid_description(cleaned_text)
                
                if score > best_score and is_valid:
                    best_description = cleaned_text
                    best_score = score
        
        # Always try to extract content by looking for job-related sections with headings first
        # This is often more accurate than generic selectors
        job_sections = self._extract_job_sections_by_headings(soup)
        if job_sections:
            combined_text = '\n\n'.join(job_sections)
            cleaned_text = self._extract_and_clean_text([soup.new_string(combined_text)])
            
            # Check if this looks like a job description
            has_nav = self._contains_navigation_patterns(cleaned_text)
            is_valid = JobPostingExtractorUtils.is_valid_description(cleaned_text)
            score = self._score_description(cleaned_text)
            
            if not has_nav and is_valid and len(cleaned_text) > 200 and score > best_score:
                best_description = cleaned_text
                best_score = score
        
        # If no description found with specific selectors or job sections, try a more intelligent approach
        if not best_description:
            
            # Look for main content areas, avoiding footer/navigation
            if not best_description:
                main_content_selectors = [
                    'main',
                    '[role="main"]',
                    '.main-content',
                    '.content',
                    '.job-content',
                    'article'
                ]
                
                main_content = None
                for selector in main_content_selectors:
                    elements = soup.select(selector)
                    if elements:
                        main_content = elements[0]
                        break
                
                if main_content:
                    # Extract text from main content, filtering out navigation
                    filtered_content = self._filter_navigation_content(main_content)
                    if filtered_content:
                        cleaned_text = self._extract_and_clean_text([filtered_content])
                        
                        # Check if this looks like a job description
                        has_nav = self._contains_navigation_patterns(cleaned_text)
                        is_valid = JobPostingExtractorUtils.is_valid_description(cleaned_text)
                        
                        if not has_nav and is_valid and len(cleaned_text) > 200:
                            best_description = cleaned_text
            
            # Fallback: try paragraphs but be more selective
            if not best_description:
                paragraphs = soup.find_all('p')
                substantial_paragraphs = []
                
                for p in paragraphs:
                    text = p.get_text().strip()
                    # More selective: look for paragraphs that seem job-related
                    if (len(text) > 150 and 
                        not self._contains_navigation_patterns(text) and
                        not text.lower().startswith(('privacy', 'terms', 'cookie', 'equal opportunity'))):
                        substantial_paragraphs.append(text)
                
                if substantial_paragraphs:
                    # Combine substantial paragraphs
                    combined_text = '\n\n'.join(substantial_paragraphs)
                    cleaned_text = self._extract_and_clean_text([soup.new_string(combined_text)])
                    
                    # Check if this looks like a job description
                    has_nav = self._contains_navigation_patterns(cleaned_text)
                    is_valid = JobPostingExtractorUtils.is_valid_description(cleaned_text)
                    
                    if not has_nav and is_valid:
                        best_description = cleaned_text
        
        return best_description
    
    def _extract_job_sections_by_headings(self, soup: BeautifulSoup) -> List[str]:
        """Extract job content by looking for sections with job-related headings"""
        job_sections = []
        
        # Look for headings that indicate job content sections
        job_heading_keywords = [
            'about the job',
            'responsibilities', 
            'minimum qualifications',
            'preferred qualifications',
            'qualifications',
            'requirements',
            'experience',
            'education',
            'skills',
            'benefits',
            'salary',
            'location',
            'job type',
            'description'
        ]
        
        # Find all headings (h1-h6)
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for heading in headings:
            heading_text = heading.get_text().strip().lower()
            
            # Check if this heading indicates a job section
            if any(keyword in heading_text for keyword in job_heading_keywords):
                # Extract content following this heading
                section_content = self._extract_content_after_heading(heading)
                if section_content and len(section_content.strip()) > 50:
                    # Add the heading and its content
                    full_section = f"{heading.get_text().strip()}\n{section_content}"
                    job_sections.append(full_section)
        
        return job_sections
    
    def _extract_content_after_heading(self, heading) -> str:
        """Extract content that follows a heading until the next heading or end of container"""
        content_parts = []
        current = heading.next_sibling
        
        # Walk through siblings until we hit another heading or run out
        while current:
            if hasattr(current, 'name'):
                # If we hit another heading, stop
                if current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                # If it's a paragraph, div, or list, include it
                if current.name in ['p', 'div', 'ul', 'ol', 'li']:
                    # Preserve HTML structure for proper list processing
                    html_content = str(current)
                    if html_content and len(html_content.strip()) > 10:
                        content_parts.append(html_content)
            else:
                # Text node
                text = str(current).strip()
                if text and len(text) > 10:
                    content_parts.append(text)
            
            current = current.next_sibling
        
        # Join the HTML content and then process it to preserve list structure
        combined_html = '\n'.join(content_parts)
        if combined_html:
            # Use the _extract_and_clean_text method to properly format lists
            soup = BeautifulSoup(combined_html, 'html.parser')
            return self._extract_and_clean_text([soup])
        
        return '\n'.join(content_parts)
    
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
            'multiple locations',
            'privacy policy',
            'terms of service',
            'cookie policy',
            'equal opportunity',
            'affirmative action',
            'workforce that is representative',
            'culture of belonging',
            'basis protected by law',
            'recruitment agencies',
            'unsolicited resumes',
            'accommodation',
            'english proficiency',
            'follow life at',
            'more about us',
            'related information',
            'investor relations',
            'send feedback',
            'help link'
        ]
        
        text_lower = text.lower()
        
        # If more than 20% of the text matches navigation patterns, it's likely navigation
        nav_matches = sum(1 for pattern in nav_patterns if pattern in text_lower)
        if nav_matches > len(nav_patterns) * 0.2:
            return True
        
        # Check if the text is too short (likely navigation)
        if len(text.strip()) < 200:
            return True
        
        # Check if it contains mostly navigation elements
        nav_words = ['apply', 'back', 'search', 'results', 'acknowledge', 'refer', 'privacy', 'terms', 'cookie', 'equal', 'opportunity']
        words = text_lower.split()
        nav_word_count = sum(1 for word in words if word in nav_words)
        
        if len(words) > 0 and nav_word_count / len(words) > 0.1:
            return True
        
        # Check if text starts with common footer patterns
        footer_starters = [
            'privacy', 'terms', 'cookie', 'equal opportunity', 'google is proud',
            'follow life at', 'more about us', 'related information', 'investor relations'
        ]
        
        for starter in footer_starters:
            if text_lower.startswith(starter):
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
        
        # Remove all remaining HTML tags and decode entities using shared utility
        text = JobPostingExtractorUtils.clean_html_tags(html_content)
        
        # Additional whitespace cleaning is handled by the shared utility
        # Replace multiple consecutive line breaks with double line breaks (paragraph breaks)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text
    
    
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
        if not JobPostingExtractorUtils._is_valid_title(title):
            return False
        
        # Description must be substantial
        if not JobPostingExtractorUtils.is_valid_description(description):
            return False
        
        return True
