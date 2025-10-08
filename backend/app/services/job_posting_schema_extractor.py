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
            # Find all JSON-LD script tags
            json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
            matches = re.findall(json_ld_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                try:
                    # Parse JSON-LD
                    data = json.loads(match.strip())
                    
                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        for item in data:
                            result = self._process_json_ld_item(item)
                            if result:
                                return result
                    else:
                        result = self._process_json_ld_item(data)
                        if result:
                            return result
                            
                except json.JSONDecodeError:
                    continue
            
            return None
            
        except Exception as e:
            logger.error("JSON-LD extraction failed", error=str(e))
            return None
    
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
            
            return {
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
                    return title
        
        return None
    
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
                        return company
        
        # Check for direct company fields
        company_fields = ['company', 'employer', 'organization']
        for field in company_fields:
            if field in item and item[field]:
                company = str(item[field]).strip()
                if len(company) > 1:
                    return company
        
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
            
            # Extract company
            company = self._extract_microdata_property(job_section, 'hiringOrganization')
            if not company:
                company = self._extract_microdata_property(job_section, 'name')
            
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
        """Clean HTML tags and entities from text"""
        # Remove HTML tags
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
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
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
