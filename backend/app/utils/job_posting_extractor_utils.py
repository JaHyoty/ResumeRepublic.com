"""
Shared utilities for job posting extractors
Contains common extraction logic used by both heuristic and schema extractors
"""

import re
from typing import Optional
from bs4 import BeautifulSoup
import structlog

logger = structlog.get_logger()


class JobPostingExtractorUtils:
    """Shared utilities for job posting extraction"""
    
    @staticmethod
    def clean_html_tags(text: str) -> str:
        """Clean HTML tags and entities while preserving line breaks and structure"""
        if not text:
            return text
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode common HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#x27;': "'",
            '&#39;': "'",
            '&#x2F;': '/',
            '&nbsp;': ' ',
            '&ndash;': '–',
            '&mdash;': '—',
            '&hellip;': '…',
            '&copy;': '©',
            '&reg;': '®',
            '&trade;': '™',
            '&bull;': '•',
            '&middot;': '·',
            '&lsquo;': ''',
            '&rsquo;': ''',
            '&ldquo;': '"',
            '&rdquo;': '"',
        }
        
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)
        
        # Clean up extra whitespace but preserve line breaks
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
    
    @staticmethod
    def clean_title(title: str) -> str:
        """Clean job title by removing text inside square brackets, HTML tags, and job IDs"""
        # Remove HTML tags first
        cleaned_title = JobPostingExtractorUtils.clean_html_tags(title)
        
        # Remove text inside square brackets (e.g., "[Multiple Positions Available]")
        cleaned_title = re.sub(r'\[.*?\]', '', cleaned_title).strip()
        
        # Remove job IDs and tracking parameters
        # Pattern: "Title - Job ID: 12345" or "Title - ID: 12345"
        cleaned_title = re.sub(r'\s*-\s*job\s*id\s*:?\s*\d+.*$', '', cleaned_title, flags=re.IGNORECASE)
        cleaned_title = re.sub(r'\s*-\s*id\s*:?\s*\d+.*$', '', cleaned_title, flags=re.IGNORECASE)
        
        # Remove common suffixes that might contain job IDs
        suffixes_to_remove = [
            r'\s*-\s*job\s*details.*$',
            r'\s*-\s*careers.*$',
            r'\s*-\s*jobs.*$',
            r'\s*-\s*hiring.*$',
            r'\s*-\s*employment.*$',
            r'\s*-\s*opportunities.*$',
        ]
        
        # Remove .jobs domains and similar patterns
        domain_patterns = [
            r'\s*\|\s*[^|]*\.jobs.*$',  # "| Amazon.jobs" or "| Company.jobs"
            r'\s*@\s*[^@]*\.jobs.*$',   # "@ Amazon.jobs"
            r'\s*-\s*[^-]*\.jobs.*$',   # "- Amazon.jobs"
        ]
        
        for suffix_pattern in suffixes_to_remove:
            cleaned_title = re.sub(suffix_pattern, '', cleaned_title, flags=re.IGNORECASE)
        
        # Apply domain patterns to remove .jobs domains
        for domain_pattern in domain_patterns:
            cleaned_title = re.sub(domain_pattern, '', cleaned_title, flags=re.IGNORECASE)
        
        # Clean up any extra whitespace
        cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()
        return cleaned_title
    
    @staticmethod
    def clean_company(company: str) -> str:
        """Clean company name by removing common career page suffixes and job-related patterns"""
        # Remove common career page suffixes (case insensitive)
        career_suffixes = [
            r'\s+candidate\s+experience\s+page\s*$',
            r'\s+candidate\s+experience\s*$',
            r'\s+career\s+page\s*$',
            r'\s+careers\s+page\s*$',
            r'\s+career\s+site\s*$',
            r'\s+careers\s+site\s*$',
            r'\s+career\s+portal\s*$',
            r'\s+careers\s+portal\s*$',
            r'\s+job\s+board\s*$',
            r'\s+career\s+center\s*$',
            r'\s+careers\s+center\s*$'
        ]
        
        cleaned_company = JobPostingExtractorUtils.clean_html_tags(company.strip())
        
        # Remove career-related suffixes
        for suffix_pattern in career_suffixes:
            cleaned_company = re.sub(suffix_pattern, '', cleaned_company, flags=re.IGNORECASE)
        
        # Remove job-related suffixes that might be in company names
        job_suffixes = [
            r'\s*-\s*job\s*id.*$',           # Remove job ID suffixes
            r'\s*-\s*job\s*details.*$',       # Remove job details suffixes
            r'\s*-\s*careers.*$',             # Remove careers suffixes
            r'\s*-\s*jobs.*$',                # Remove jobs suffixes
            r'\s*-\s*hiring.*$',              # Remove hiring suffixes
            r'\s*careers?\s*$',               # Remove "careers" suffix
            r'\s*jobs?\s*$',                 # Remove "jobs" suffix
            r'\s*hiring\s*$',                # Remove "hiring" suffix
        ]
        
        for suffix_pattern in job_suffixes:
            cleaned_company = re.sub(suffix_pattern, '', cleaned_company, flags=re.IGNORECASE)
        
        # Remove everything after common separators (in case company name was extracted from title patterns)
        separators = [
            r'\s*at\s+.*$',                  # Remove everything after "at"
            r'\s*@\s+.*$',                   # Remove everything after "@"
            r'\s*-\s+.*$',                   # Remove everything after "-"
            r'\s*:\s+.*$',                   # Remove everything after ":"
            r'\s*[—|]\s+.*$',                # Remove everything after "—" or "|"
        ]
        
        for separator_pattern in separators:
            cleaned_company = re.sub(separator_pattern, '', cleaned_company, flags=re.IGNORECASE)
        
        # Clean up any extra whitespace and trailing punctuation
        cleaned_company = re.sub(r'\s+', ' ', cleaned_company).strip()
        cleaned_company = re.sub(r'\s*-\s*$', '', cleaned_company)       # Remove trailing dashes
        cleaned_company = re.sub(r'\.\s*$', '', cleaned_company)         # Remove trailing dots
        cleaned_company = re.sub(r'\s*\(.*\)\s*$', '', cleaned_company)   # Remove parenthetical content
        
        # Remove specific domain suffixes (after other cleanup)
        domain_suffixes = [
            r'\.jobs\s*$',                    # Remove ".jobs" suffix
            r'\.careers\s*$',                  # Remove ".careers" suffix
            r'\.hiring\s*$',                   # Remove ".hiring" suffix
        ]
        
        for suffix_pattern in domain_suffixes:
            cleaned_company = re.sub(suffix_pattern, '', cleaned_company, flags=re.IGNORECASE)
        
        return cleaned_company
    
    @staticmethod
    def extract_title_and_company_from_page_title(soup: BeautifulSoup, extractor_name: str = "extractor") -> tuple[Optional[str], Optional[str]]:
        """Extract both job title and company from page title using common patterns"""
        # Get page title
        title_tag = soup.find('title')
        if not title_tag or not title_tag.get_text():
            return None, None
        
        title_text = title_tag.get_text().strip()
        logger.info(f"{extractor_name} analyzing page title: '{title_text}'")
        
        # Extract title using patterns
        title = JobPostingExtractorUtils._extract_title_from_page_title(title_text)
        
        # Extract company using patterns
        company = JobPostingExtractorUtils._extract_company_from_title_text(title_text, extractor_name)
        
        return title, company
    
    @staticmethod
    def _extract_company_from_title_text(title_text: str, extractor_name: str) -> Optional[str]:
        """Helper function to extract company name from page title text using patterns"""
        # Common patterns for company names in titles (ordered by reliability)
        patterns = [
            # Most reliable: explicit company indicators
            r'at\s+([A-Z][A-Za-z\s&.,-]+?)(?:\s*[-|]\s*|$)',  # "Job at Company Name -" or "Job at Company Name"
            r'@\s+([A-Z][A-Za-z\s&.,-]+?)(?:\s*[-|]\s*|$)',   # "Job @ Company Name -" or "Job @ Company Name"
            r'with\s+([A-Z][A-Za-z\s&.,-]+?)(?:\s*[-|]\s*|$)', # "Job with Company Name -" or "Job with Company Name"
            r'for\s+([A-Z][A-Za-z\s&.,-]+?)(?:\s*[-|]\s*|$)',  # "Job for Company Name -" or "Job for Company Name"
            
            # Handle "| Company.jobs" pattern (like Amazon.jobs)
            r'\|\s*([A-Z][A-Za-z\s&.,-]+?)\.jobs\s*$',        # "| Company.jobs"
            r'\|\s*([A-Z][A-Za-z\s&.,-]+?)\.careers\s*$',     # "| Company.careers"
            r'\|\s*([A-Z][A-Za-z\s&.,-]+?)\.hiring\s*$',      # "| Company.hiring"
            r'\|\s*([A-Z][A-Za-z\s&.,-]+?)\s*$',              # "| Company" (fallback)
            
            # Alternative patterns
            r'([A-Z][A-Za-z\s&.,-]+?)\s*[-|]\s*careers?',     # "Company Name - Careers"
            r'([A-Z][A-Za-z\s&.,-]+?)\s*[-|]\s*jobs?',        # "Company Name - Jobs"
            r'([A-Z][A-Za-z\s&.,-]+?)\s*careers?',            # "Company Name Careers"
            r'([A-Z][A-Za-z\s&.,-]+?)\s*jobs?',               # "Company Name Jobs"
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, title_text, re.IGNORECASE)
            if match:
                potential_company = match.group(1).strip()
                logger.info(f"{extractor_name} pattern {i+1} matched: '{potential_company}'")
                
                potential_company = JobPostingExtractorUtils.clean_company(potential_company)
                logger.info(f"{extractor_name} cleaned company name: '{potential_company}'")
                
                # Validate the extracted company name
                if JobPostingExtractorUtils.is_valid_company(potential_company):
                    return JobPostingExtractorUtils.clean_company(potential_company)
                else:
                    logger.info(f"{extractor_name} invalid company name: '{potential_company}'")
        
        logger.info(f"{extractor_name} no valid company found in page title")
        return None
    
    @staticmethod
    def is_valid_company(company: str) -> bool:
        """Check if a company name is valid"""
        if not company or len(company.strip()) < 2:
            return False
        
        company_lower = company.lower().strip()
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'^(careers?|jobs?|hiring|recruitment)$',
            r'^(candidate\s+experience|candidate\s+portal)$',
            r'^(job\s+board|job\s+portal)$',
            r'^(career\s+site|careers?\s+page)$',
            r'^(apply\s+now|apply\s+here)$',
            r'^(home|about|contact|privacy|terms)$',
            r'^(job\s+details?|job\s+description)$',
            r'^(search\s+results?|more\s+about\s+us)$',
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, company_lower):
                return False
        
        # Check for job title patterns (these are not company names)
        job_title_patterns = [
            r'^(software\s+engineer|developer|programmer)$',
            r'^(data\s+scientist|analyst|consultant)$',
            r'^(product\s+manager|project\s+manager)$',
            r'^(delivery\s+consultant|technical\s+consultant)$',
            r'^(senior\s+|junior\s+|lead\s+|principal\s+)',
            r'^(associate\s+|staff\s+|director\s+)',
            r'^(cloud\s+developer|devops\s+engineer)$',
            r'^(professional\s+services|technical\s+services)$',
        ]
        
        for pattern in job_title_patterns:
            if re.match(pattern, company_lower):
                return False
        
        # Must be at least 2 characters and not just numbers
        if len(company.strip()) < 2 or company.strip().isdigit():
            return False
        
        return True
    
    
    @staticmethod
    def _extract_title_from_page_title(page_title: str) -> Optional[str]:
        """Extract job title from page title using various patterns"""
        if not page_title:
            return None
        
        # Pattern 1: "Job Title — Company Careers" or "Job Title | Company Careers"
        patterns = [
            r'^(.+?)\s*[—|]\s*.+careers.*$',  # Job Title — Company Careers
            r'^(.+?)\s*[—|]\s*.+jobs.*$',     # Job Title — Company Jobs
            r'^(.+?)\s*[—|]\s*.+career.*$',   # Job Title — Company Career
            r'^(.+?)\s*[—|]\s*.+hiring.*$',   # Job Title — Company Hiring
            r'^(.+?)\s*[—|]\s*.+employment.*$', # Job Title — Company Employment
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_title, re.IGNORECASE)
            if match:
                potential_title = match.group(1).strip()
                if JobPostingExtractorUtils._is_valid_title(potential_title):
                    return JobPostingExtractorUtils.clean_title(potential_title)
        
        # Pattern 2: "Position at Company" or "Position - Company"
        at_patterns = [
            r'^(.+?)\s+at\s+.+$',           # Position at Company
            r'^(.+?)\s*@\s*.+$',             # Position @ Company
            r'^(.+?)\s*-\s*.+$',            # Position - Company
            r'^(.+?)\s*:\s*.+$',            # Position: Company
        ]
        
        for pattern in at_patterns:
            match = re.search(pattern, page_title, re.IGNORECASE)
            if match:
                potential_title = match.group(1).strip()
                if JobPostingExtractorUtils._is_valid_title(potential_title) and len(potential_title) > 5:
                    return JobPostingExtractorUtils.clean_title(potential_title)
        
        # Pattern 3: Remove common suffixes
        suffix_patterns = [
            r'^(.+?)\s*-\s*job\s*id.*$',     # Remove job ID suffixes
            r'^(.+?)\s*-\s*job\s*details.*$', # Remove job details suffixes
            r'^(.+?)\s*-\s*careers.*$',      # Remove careers suffixes
            r'^(.+?)\s*-\s*jobs.*$',         # Remove jobs suffixes
            r'^(.+?)\s*-\s*hiring.*$',       # Remove hiring suffixes
        ]
        
        for pattern in suffix_patterns:
            match = re.search(pattern, page_title, re.IGNORECASE)
            if match:
                potential_title = match.group(1).strip()
                if JobPostingExtractorUtils._is_valid_title(potential_title) and len(potential_title) > 5:
                    return JobPostingExtractorUtils.clean_title(potential_title)
        
        return None
    
    @staticmethod
    def _is_valid_title(title: str) -> bool:
        """Validate job title"""
        if not title or len(title) <= 5:
            return False
        return True
    
    @staticmethod
    def is_valid_description(description: str) -> bool:
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
