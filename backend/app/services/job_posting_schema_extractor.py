"""
Job posting schema extractor
Extracts job data from structured markup (JSON-LD, microdata)
"""

import json
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import structlog

from app.services.job_posting_web_scraper import JobPostingWebScraper

logger = structlog.get_logger()


class JobPostingSchemaExtractor:
    """Extracts job posting data from structured markup"""
    
    def __init__(self):
        self.web_scraper = JobPostingWebScraper()
    
    async def extract_job_data(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract job data using schema.org structured markup
        Returns dict with title, company, description, confidence, and provenance
        """
        try:
            # Fetch HTML content
            html_content = await self.web_scraper.fetch_html(url)
            if not html_content:
                return None
            
            # Try JSON-LD extraction first
            json_ld_result = self._extract_from_json_ld(html_content)
            if json_ld_result:
                return json_ld_result
            
            # Try microdata extraction
            microdata_result = self._extract_from_microdata(html_content)
            if microdata_result:
                return microdata_result
            
            return None
            
        except Exception as e:
            logger.error("Schema extraction failed", url=url, error=str(e))
            return None
    
    def _extract_from_json_ld(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract job data from JSON-LD structured data"""
        try:
            # Find all JSON-LD script tags - use non-greedy matching to get complete blocks
            json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            matches = re.findall(json_ld_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for i, match in enumerate(matches):
                try:
                    # Clean up the JSON-LD content before parsing
                    cleaned_json = self._clean_json_ld_content(match.strip())
                    
                    # Parse JSON-LD
                    data = json.loads(cleaned_json)
                    
                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        for j, item in enumerate(data):
                            result = self._process_json_ld_item(item)
                            if result:
                                return result
                    else:
                        result = self._process_json_ld_item(data)
                        if result:
                            return result
                            
                except json.JSONDecodeError as e:
                    # Try to fix common JSON issues and retry
                    try:
                        fixed_json = self._fix_json_ld_issues(match.strip())
                        data = json.loads(fixed_json)
                        
                        if isinstance(data, list):
                            for j, item in enumerate(data):
                                result = self._process_json_ld_item(item)
                                if result:
                                    return result
                        else:
                            result = self._process_json_ld_item(data)
                            if result:
                                return result
                    except json.JSONDecodeError:
                        continue
            
            logger.warning("No valid JSON-LD data found in any script tags")
            return None
            
        except Exception as e:
            logger.error("JSON-LD extraction failed with exception", error=str(e))
            return None
    
    def _clean_json_ld_content(self, json_content: str) -> str:
        """Clean JSON-LD content for better parsing"""
        # Remove any leading/trailing whitespace
        json_content = json_content.strip()
        
        # Remove any BOM or invisible characters
        json_content = json_content.encode('utf-8').decode('utf-8-sig')
        
        return json_content
    
    def _fix_json_ld_issues(self, json_content: str) -> str:
        """Attempt to fix common JSON-LD parsing issues"""
        try:
            # Check if JSON appears to be truncated
            if json_content.count('{') > json_content.count('}'):
                # JSON appears to be truncated, try to close it
                # Find the last complete object/array and close it
                brace_count = 0
                last_complete_pos = -1
                
                for i, char in enumerate(json_content):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            last_complete_pos = i
                
                if last_complete_pos > 0:
                    # Truncate at the last complete position
                    json_content = json_content[:last_complete_pos + 1]
            
            # Fix unescaped quotes in HTML attributes within JSON strings
            # This handles cases like: "description": "<p style="text-align: left;">"
            
            # Find all string values that contain HTML
            def fix_html_in_string(match):
                key = match.group(1)
                value = match.group(2)
                
                # If the value contains HTML, escape quotes in HTML attributes
                if '<' in value and '>' in value:
                    # Escape quotes in HTML attributes
                    # Pattern: attribute="value" -> attribute=\"value\"
                    value = re.sub(r'(\w+)="([^"]*)"', r'\1=\\"\\2\\"', value)
                
                return f'"{key}": "{value}"'
            
            # Match JSON string pairs that contain HTML
            json_content = re.sub(r'"([^"]+)":\s*"([^"]*<[^>]*>[^"]*)"', fix_html_in_string, json_content)
            
            return json_content
            
        except Exception:
            # If fixing fails, return original content
            return json_content
    
    def _process_json_ld_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single JSON-LD item for job posting data"""
        try:
            # Check if this is a JobPosting schema
            if not self._is_job_posting_schema(item):
                return None
            
            # Extract job title
            title = self._extract_title_from_json_ld(item)
            if not title:
                return None
            
            # Extract company name
            company = self._extract_company_from_json_ld(item)
            
            # Extract job description
            description = self._extract_description_from_json_ld(item)
            if not description:
                return None
            
            # Calculate confidence based on data completeness
            confidence = self._calculate_schema_confidence(item, title, company, description)
            
            result = {
                'title': title,
                'company': company or 'Unknown Company',
                'description': description,
                'confidence': confidence,
                'excerpt': description[:200] + '...' if len(description) > 200 else description,
                'provenance': {
                    'method': 'json_ld',
                    'schema_type': item.get('@type', 'Unknown'),
                    'source': 'structured_data'
                }
            }
            
            return result
            
        except Exception as e:
            logger.error("JSON-LD item processing failed", error=str(e))
            return None
    
    def _is_job_posting_schema(self, item: Dict[str, Any]) -> bool:
        """Check if JSON-LD item represents a job posting"""
        schema_type = item.get('@type', '')
        if isinstance(schema_type, list):
            schema_type = ' '.join(schema_type)
        
        job_posting_types = [
            'JobPosting',
            'jobposting',
            'JobPostingSchema',
            'https://schema.org/JobPosting',
            'http://schema.org/JobPosting'
        ]
        
        return any(job_type.lower() in schema_type.lower() for job_type in job_posting_types)
    
    def _extract_title_from_json_ld(self, item: Dict[str, Any]) -> Optional[str]:
        """Extract job title from JSON-LD item"""
        title_fields = ['title', 'jobTitle', 'name', 'headline']
        
        for field in title_fields:
            if field in item and item[field]:
                title = str(item[field]).strip()
                if len(title) > 2:
                    return self._clean_title(title)
        
        return None
    
    def _clean_title(self, title: str) -> str:
        """Clean job title by removing text inside square brackets"""
        import re
        # Remove text inside square brackets (e.g., "[Multiple Positions Available]")
        cleaned_title = re.sub(r'\[.*?\]', '', title).strip()
        # Clean up any extra whitespace
        cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()
        return cleaned_title
    
    def _clean_company(self, company: str) -> str:
        """Clean company name by removing common career page suffixes"""
        import re
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
        
        cleaned_company = company.strip()
        for suffix_pattern in career_suffixes:
            cleaned_company = re.sub(suffix_pattern, '', cleaned_company, flags=re.IGNORECASE)
        
        # Clean up any extra whitespace
        cleaned_company = re.sub(r'\s+', ' ', cleaned_company).strip()
        return cleaned_company
    
    def _extract_company_from_json_ld(self, item: Dict[str, Any]) -> Optional[str]:
        """Extract company name from JSON-LD item"""
        # Check for hiringOrganization
        hiring_org = item.get('hiringOrganization', {})
        
        if isinstance(hiring_org, dict):
            company_fields = ['name', 'legalName', 'alternateName']
            for field in company_fields:
                if field in hiring_org and hiring_org[field]:
                    company = str(hiring_org[field]).strip()
                    if len(company) > 1:
                        return self._clean_company(company)
        
        # Check for direct company fields
        company_fields = ['company', 'employer', 'organization']
        for field in company_fields:
            if field in item and item[field]:
                company = str(item[field]).strip()
                if len(company) > 1:
                    return self._clean_company(company)
        
        return None
    
    def _extract_description_from_json_ld(self, item: Dict[str, Any]) -> Optional[str]:
        """Extract job description from JSON-LD item"""
        description_fields = ['description', 'jobDescription', 'summary', 'responsibilities']
        
        for field in description_fields:
            if field in item and item[field]:
                description = str(item[field]).strip()
                if len(description) > 50:  # Must be substantial
                    return self._clean_html_from_text(description)
        
        return None
    
    def _extract_from_microdata(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract job data from microdata attributes"""
        try:
            # This is a simplified microdata extractor
            # In a full implementation, you'd use a proper microdata parser
            
            # Look for itemtype="http://schema.org/JobPosting"
            job_posting_pattern = r'<[^>]*itemtype=["\']http://schema\.org/JobPosting["\'][^>]*>(.*?)</[^>]*>'
            match = re.search(job_posting_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            if not match:
                return None
            
            job_section = match.group(1)
            
            # Extract title
            title = self._extract_microdata_property(job_section, 'jobTitle')
            if not title:
                title = self._extract_microdata_property(job_section, 'title')
            
            if not title:
                return None
            
            # Clean the title
            title = self._clean_title(title)
            
            # Extract company
            company = self._extract_microdata_property(job_section, 'hiringOrganization')
            if not company:
                company = self._extract_microdata_property(job_section, 'name')
            
            # Clean the company name
            if company:
                company = self._clean_company(company)
            
            # Extract description
            description = self._extract_microdata_property(job_section, 'description')
            if not description:
                description = self._extract_microdata_property(job_section, 'jobDescription')
            
            if not description or len(description) < 50:
                return None
            
            return {
                'title': title,
                'company': company or 'Unknown Company',
                'description': self._clean_html_from_text(description),
                'confidence': 0.7,  # Lower confidence for microdata
                'excerpt': description[:200] + '...' if len(description) > 200 else description,
                'provenance': {
                    'method': 'microdata',
                    'schema_type': 'JobPosting',
                    'source': 'structured_data'
                }
            }
            
        except Exception as e:
            logger.error("Microdata extraction failed", error=str(e))
            return None
    
    def _extract_microdata_property(self, html_section: str, property_name: str) -> Optional[str]:
        """Extract a specific property from microdata HTML"""
        pattern = rf'<[^>]*itemprop=["\']?{property_name}["\']?[^>]*>(.*?)</[^>]*>'
        match = re.search(pattern, html_section, re.DOTALL | re.IGNORECASE)
        
        if match:
            content = match.group(1).strip()
            # Remove HTML tags
            content = re.sub(r'<[^>]+>', '', content)
            return content if content else None
        
        return None
    
    def _clean_html_from_text(self, text: str) -> str:
        """Clean HTML tags and entities from text while preserving paragraph structure and formatting lists"""
        # First, handle specific HTML elements to preserve structure
        # Convert </p> tags to double line breaks (paragraph breaks)
        text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
        
        # Convert <br> and <br/> tags to single line breaks
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        
        # Handle list items - convert <li> to bullet points
        # First, handle unordered lists <ul> and <ol> - add spacing around them
        text = re.sub(r'<(ul|ol)[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</(ul|ol)>', '\n', text, flags=re.IGNORECASE)
        
        # Convert <li> tags to bullet points with proper formatting
        text = re.sub(r'<li[^>]*>', '\n- ', text, flags=re.IGNORECASE)
        text = re.sub(r'</li>', '', text, flags=re.IGNORECASE)
        
        # Handle other block elements that should have line breaks
        block_elements = ['div', 'section', 'article', 'header', 'footer', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        for element in block_elements:
            # Add line break after opening tags
            text = re.sub(f'<{element}[^>]*>', f'\n', text, flags=re.IGNORECASE)
            # Add line break before closing tags
            text = re.sub(f'</{element}>', '\n', text, flags=re.IGNORECASE)
        
        # Remove all remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
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
    
    def _calculate_schema_confidence(self, item: Dict[str, Any], title: str, company: str, description: str) -> float:
        """Calculate confidence score for schema extraction"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for complete data
        if title and len(title) > 5:
            confidence += 0.2
        if company and len(company) > 2:
            confidence += 0.1
        if description and len(description) > 100:
            confidence += 0.2
        
        # Increase confidence for specific schema fields
        if 'hiringOrganization' in item:
            confidence += 0.1
        if 'jobDescription' in item:
            confidence += 0.1
        if 'datePosted' in item:
            confidence += 0.05
        
        return min(confidence, 1.0)
