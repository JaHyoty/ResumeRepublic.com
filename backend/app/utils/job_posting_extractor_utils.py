"""
Shared utilities for job posting extractors
Contains common extraction logic used by both heuristic and schema extractors
"""

import re
from typing import Optional
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
        """Clean job title by removing text inside square brackets and HTML tags"""
        # Remove HTML tags first
        cleaned_title = JobPostingExtractorUtils.clean_html_tags(title)
        
        # Remove text inside square brackets (e.g., "[Multiple Positions Available]")
        cleaned_title = re.sub(r'\[.*?\]', '', cleaned_title).strip()
        
        # Clean up any extra whitespace
        cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()
        return cleaned_title
    
    @staticmethod
    def clean_company(company: str) -> str:
        """Clean company name by removing common career page suffixes"""
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
        for suffix_pattern in career_suffixes:
            cleaned_company = re.sub(suffix_pattern, '', cleaned_company, flags=re.IGNORECASE)
        
        # Clean up any extra whitespace
        cleaned_company = re.sub(r'\s+', ' ', cleaned_company).strip()
        return cleaned_company
    
    @staticmethod
    def extract_company_from_title(soup, extractor_name: str = "extractor") -> Optional[str]:
        """Extract company name from page title using common patterns"""
        # Get page title
        title_tag = soup.find('title')
        if not title_tag or not title_tag.get_text():
            return None
        
        title = title_tag.get_text().strip()
        logger.info(f"{extractor_name} analyzing page title for company: '{title}'")
        
        # Common patterns for company names in titles (ordered by reliability)
        patterns = [
            # Most reliable: explicit company indicators
            r'at\s+([A-Z][A-Za-z\s&.,-]+?)(?:\s*[-|]\s*|$)',  # "Job at Company Name -" or "Job at Company Name"
            r'@\s+([A-Z][A-Za-z\s&.,-]+?)(?:\s*[-|]\s*|$)',   # "Job @ Company Name -" or "Job @ Company Name"
            r'with\s+([A-Z][A-Za-z\s&.,-]+?)(?:\s*[-|]\s*|$)', # "Job with Company Name -" or "Job with Company Name"
            r'for\s+([A-Z][A-Za-z\s&.,-]+?)(?:\s*[-|]\s*|$)',  # "Job for Company Name -" or "Job for Company Name"
            
            # Alternative patterns
            r'([A-Z][A-Za-z\s&.,-]+?)\s*[-|]\s*careers?',     # "Company Name - Careers"
            r'([A-Z][A-Za-z\s&.,-]+?)\s*[-|]\s*jobs?',        # "Company Name - Jobs"
            r'([A-Z][A-Za-z\s&.,-]+?)\s*careers?',            # "Company Name Careers"
            r'([A-Z][A-Za-z\s&.,-]+?)\s*jobs?',               # "Company Name Jobs"
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                logger.info(f"{extractor_name} pattern {i+1} matched: '{company}'")
                
                # Clean up common suffixes
                company = re.sub(r'\s*[-|]\s*.*$', '', company)  # Remove everything after "-" or "|"
                company = re.sub(r'\s*\(.*\)\s*$', '', company)   # Remove parenthetical content
                company = re.sub(r'\s*-\s*$', '', company)       # Remove trailing dashes
                company = re.sub(r'\s*careers?\s*$', '', company, flags=re.IGNORECASE)  # Remove "careers" suffix
                company = re.sub(r'\s*jobs?\s*$', '', company, flags=re.IGNORECASE)    # Remove "jobs" suffix
                
                logger.info(f"{extractor_name} cleaned company name: '{company}'")
                
                # Validate the extracted company name
                if JobPostingExtractorUtils.is_valid_company(company):
                    logger.info(f"{extractor_name} valid company found: '{company}'")
                    return JobPostingExtractorUtils.clean_company(company)
                else:
                    logger.info(f"{extractor_name} invalid company name: '{company}'")
        
        logger.info(f"{extractor_name} no valid company found in page title")
        return None
    
    @staticmethod
    def is_valid_company(company: str) -> bool:
        """Check if a company name is valid"""
        if not company or len(company.strip()) < 2:
            return False
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'^(careers?|jobs?|hiring|recruitment)$',
            r'^(candidate\s+experience|candidate\s+portal)$',
            r'^(job\s+board|job\s+portal)$',
            r'^(career\s+site|careers?\s+page)$',
            r'^(apply\s+now|apply\s+here)$',
            r'^(home|about|contact|privacy|terms)$',
        ]
        
        company_lower = company.lower().strip()
        for pattern in invalid_patterns:
            if re.match(pattern, company_lower):
                return False
        
        return True
