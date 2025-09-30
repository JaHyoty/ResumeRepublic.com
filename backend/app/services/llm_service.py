"""
LLM Service for resume generation
"""

import os
import httpx
import logging
import ssl
from typing import Dict, Any
from app.core.settings import settings
from app.utils.tls_utils import create_httpx_client, validate_tls_configuration

# Use structlog for consistent logging
import structlog
logger = structlog.get_logger(__name__)


class LLMService:
    def __init__(self):
        # Use unified configuration (handles SSM, env vars, and defaults)
        self.api_key = settings.OPENROUTER_API_KEY
        self.llm_model = settings.OPENROUTER_LLM_MODEL or "anthropic/claude-3.5-sonnet"
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        # Validate TLS configuration
        if not validate_tls_configuration():
            logger.warning("TLS configuration validation failed, but continuing with current settings")

        # Debug logging
        if not self.api_key:
            print("WARNING: OPENROUTER_API_KEY is not set!")
        else:
            print(f"OpenRouter API key loaded: {self.api_key[:10]}...")
        print(f"Using LLM model: {self.llm_model}")
        if settings.ENFORCE_TLS:
            print(f"TLS enforcement enabled for LLM API calls (min version: {settings.MIN_TLS_VERSION})")
        else:
            print("WARNING: TLS enforcement is disabled for LLM API calls")
    
    async def generate_resume(
        self, 
        job_title: str,
        job_description: str,
        applicant_data: Dict[str, Any],
        template_content: str,
        locale: str = "en-US"
    ) -> str:
        """
        Generate optimized resume using LLM
        """
        
        # Validate API key
        if not self.api_key:
            raise Exception("OPENROUTER_API_KEY is not configured. Please set the environment variable.")
        
        # Format applicant data for the prompt
        applicant_knowledge = self._format_applicant_data(applicant_data)
        
        prompt = f"""You are a professional resume writer. Generate an optimized resume in LaTeX format for a {job_title} position.

CRITICAL REQUIREMENTS:
- Use ONLY the provided LaTeX template structure
- Replace template content with applicant's information
- Highlight keywords from the job description
- Do NOT add explanations, comments, or markdown formatting
- Return ONLY valid LaTeX code starting with \\begin{{document}} and ending with \\end{{document}}

FORMATTING REQUIREMENTS:
1. MULTI-POSITION FORMATTING:
   - If an applicant has multiple positions at the same company, use the multi-position format from the template
   - First position: Use \\resumeSubheading with company name and location
   - Additional positions at same company: Use \\resumeSubSubheading (without repeating company name)
   - Group all positions under the same company together

2. KEYWORD INTEGRATION:
   - You have creative freedom to rephrase and optimize experience descriptions
   - Integrate relevant keywords from the job description naturally into descriptions
   - Enhance descriptions while maintaining factual accuracy
   - Use action verbs and quantifiable results when possible
   - Make descriptions more compelling and ATS-friendly

3. PHONE NUMBER FORMATTING:
   - Format phone numbers according to the specified locale: {locale}
   - Use appropriate regional formatting for professional presentation
   - Examples by locale:
     * en-US/en-CA: (555) 123-4567 or +1 (555) 123-4567
     * en-GB/en-AU: 0123 456 789 or +44 123 456 789
     * fr-FR: 01 23 45 67 89 or +33 1 23 45 67 89
     * de-DE: 030 12345678 or +49 30 12345678
     * es-ES/es-MX: 123 456 789 or +34 123 456 789
     * For other locales, use international format: +[country code] [number]
   - Ensure the phone number looks professional and follows regional conventions

ACCURACY REQUIREMENTS:
1. Use ONLY knowledge found from the applicant's history:
   - Skills section must contain ONLY skills present in the applicant's skills list
   - Experience section must NOT claim accomplishments the applicant has not claimed
   - Experience section must use ONLY skills found in the applicant's skills
   - Certifications section must use EXACT naming from the applicant's certifications

2. Education:
   - MANDATORY: Use the Graduation Date field EXACTLY as provided in the applicant data
   - FORBIDDEN: Do NOT use "N/A", "Current", "Present", "In Progress", or any placeholder text
   - FORBIDDEN: Do NOT modify, abbreviate, or change the Graduation Date format in any way
   - EXAMPLE: If Graduation Date shows "Expected May 2025", you MUST display "Expected May 2025" exactly
   - EXAMPLE: If Graduation Date shows "June 2023", you MUST display "June 2023" exactly
   - If Graduation Date is null/empty, leave the date field empty - do NOT add placeholder text
   - Do not display the location for education
   - GPA FORMATTING: If GPA is a number, display it with exactly 2 decimal places (e.g., "3.85", "4.00"). If GPA is text (e.g., "First Class", "Magna Cum Laude"), display as-is.

3. Experience:
   - MANDATORY: display the location of every experience, even if Remote
   - MANDATORY: Select only one job title for an experience. Choose the most relevant title.
   - FORBIDDEN: Do NOT repeat job titles for an experience. One experience can have only one job title.

4. Project dates:
   - Do NOT show any dates for projects
   - Use a blank space ' ' for the date parameter
   
5. Avoid vague adjectives - use only hard truths and specific facts

JOB DESCRIPTION:
{job_description}

APPLICANT INFORMATION:
{applicant_knowledge}

LATEX TEMPLATE:
{template_content}

Generate the optimized resume now."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.llm_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            # Debug: Log TLS usage before making request
            logger.info("Making LLM API request", 
                       url=self.base_url, 
                       using_https=self.base_url.startswith('https://'),
                       timeout=60.0)
            
            # Use httpx client with TLS enforcement
            async with create_httpx_client() as client:
                response = await client.post(self.base_url, headers=headers, json=data)
                
                # Debug: Log response details
                logger.info("LLM API response received",
                           status_code=response.status_code,
                           using_https=str(response.url).startswith('https://'),
                           content_length=len(response.content))
            
            # Handle specific HTTP status codes
            if response.status_code == 401:
                raise Exception("OpenRouter API authentication failed. Please check your OPENROUTER_API_KEY.")
            elif response.status_code == 403:
                raise Exception("OpenRouter API access forbidden. Please check your API key permissions.")
            elif response.status_code == 429:
                raise Exception("OpenRouter API rate limit exceeded. Please try again later.")
            
            response.raise_for_status()
            
            result = response.json()
            
            # Check for OpenRouter-specific error responses
            if "error" in result:
                error_msg = result["error"].get("message", "Unknown error")
                raise Exception(f"OpenRouter API error: {error_msg}")
            
            # Extract content from response
            if "choices" in result and len(result["choices"]) > 0:
                raw_content = result["choices"][0]["message"]["content"]
                logger.debug(f"Raw LLM response length: {len(raw_content)}")
                logger.debug(f"Raw LLM response preview: {raw_content[:500]}...")
                # Clean up the response to extract only LaTeX code
                cleaned_content = self._extract_latex_content(raw_content)
                logger.debug(f"Cleaned LaTeX content length: {len(cleaned_content)}")
                logger.debug(f"Cleaned LaTeX content preview: {cleaned_content[:500]}...")
                return cleaned_content
            else:
                raise Exception("No response content received from OpenRouter API")
            
        except httpx.ConnectError as e:
            if "SSL" in str(e) or "TLS" in str(e) or "certificate" in str(e).lower():
                logger.error(f"TLS connection error to OpenRouter API: {str(e)}")
                raise Exception(f"TLS connection failed to OpenRouter API. Please check your network configuration and SSL settings. Error: {str(e)}")
            else:
                logger.error(f"Connection error to OpenRouter API: {str(e)}")
                raise Exception(f"Failed to connect to OpenRouter API. Please check your network connection. Error: {str(e)}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception("OpenRouter API authentication failed. Please check your OPENROUTER_API_KEY.")
            else:
                logger.error(f"HTTP error to OpenRouter API: {e.response.status_code} - {str(e)}")
                raise Exception(f"OpenRouter API request failed: {e.response.status_code} - {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"Request error to OpenRouter API: {str(e)}")
            raise Exception(f"OpenRouter API request failed: {str(e)}")
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error to OpenRouter API: {str(e)}")
            raise Exception(f"OpenRouter API request timed out. Please try again later. Error: {str(e)}")
        except ssl.SSLError as e:
            logger.error(f"SSL error when connecting to OpenRouter API: {str(e)}")
            raise Exception(f"SSL certificate verification failed for OpenRouter API. Error: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected response format from OpenRouter API: {str(e)}")
    
    def _extract_latex_content(self, raw_content: str) -> str:
        """
        Extract only the LaTeX code from the LLM response, removing any explanations or markdown
        """
        # Look for \begin{document} in the content
        begin_doc_index = raw_content.find('\\begin{document}')
        
        if begin_doc_index == -1:
            # If no \begin{document} found, try to find it without backslashes
            begin_doc_index = raw_content.find('begin{document}')
            if begin_doc_index != -1:
                # Found it without backslashes, add them back
                latex_content = raw_content[begin_doc_index:]
                latex_content = latex_content.replace('begin{document}', '\\begin{document}')
                latex_content = latex_content.replace('end{document}', '\\end{document}')
            else:
                # If still not found, return the content as-is
                return raw_content.strip()
        else:
            # Extract everything from \begin{document} onwards
            latex_content = raw_content[begin_doc_index:]
        
        # Remove any trailing explanations or markdown
        # Only look for patterns that are clearly outside LaTeX content
        end_patterns = [
            '```',
            '---',
            '## ',
            '**Note:',
            'Note:',
            'The above',
            'This LaTeX'
        ]
        
        # Only apply pattern matching if we're sure it's outside the LaTeX content
        # Look for patterns that appear after \end{document}
        end_doc_index = latex_content.find('\\end{document}')
        if end_doc_index != -1:
            # Only check for patterns after \end{document}
            content_after_end = latex_content[end_doc_index + len('\\end{document}'):]
            for pattern in end_patterns:
                pattern_index = content_after_end.find(pattern)
                if pattern_index != -1:
                    # Remove content after the pattern
                    latex_content = latex_content[:end_doc_index + len('\\end{document}') + pattern_index].strip()
                    break
        
        # Ensure the content ends with \end{document}
        if not latex_content.strip().endswith('\\end{document}'):
            # Try to find \end{document} and truncate after it
            end_doc_index = latex_content.find('\\end{document}')
            if end_doc_index != -1:
                latex_content = latex_content[:end_doc_index + len('\\end{document}')]
            else:
                # If no \end{document} found, add it
                latex_content = latex_content.strip() + '\n\\end{document}'
        
        return latex_content.strip()
    
    async def analyze_keywords(self, job_description: str) -> list[str]:
        """
        Analyze job description to extract key skills and keywords
        """
        
        # Validate API key
        if not self.api_key:
            raise Exception("OPENROUTER_API_KEY is not configured. Please set the environment variable.")
        
        prompt = f"""You are a professional resume analyst. Analyze the following job description and extract ONLY the technical skills, tools, technologies, and keywords that are EXPLICITLY MENTIONED in the text.

CRITICAL REQUIREMENTS:
- Extract ONLY keywords that are DIRECTLY STATED in the job description text
- Do NOT infer, assume, or add related skills that are not explicitly mentioned
- Do NOT include soft skills, general terms, job requirements, education majors, or degree requirements
- Return ONLY a JSON array of strings, no explanations or additional text
- Each skill must be a specific, searchable keyword that appears in the job description
- Maximum 20 keywords, but ONLY return what is actually present in the text
- If there are only 3-5 technical terms mentioned, return only those 3-5 terms
- Use proper capitalization and exact naming conventions as they appear in the job description

STRICT EXTRACTION RULES:
- ONLY extract terms that are literally present in the job description
- Do NOT add synonyms or related technologies (e.g., if "React" is mentioned, don't add "JavaScript" unless it's also mentioned)
- Do NOT add common tools that "might be used" with mentioned technologies
- Do NOT pad the list with generic terms to reach a target number
- If the job description mentions very few technical terms, return a short list

EXAMPLES of what TO INCLUDE (only if explicitly mentioned):
- Programming languages: "Python", "JavaScript", "Java", "C++"
- Frameworks: "React", "Angular", "Django", "Spring Boot"
- Tools: "Docker", "Kubernetes", "Git", "Jenkins"
- Technologies: "AWS", "PostgreSQL", "Redis", "GraphQL"
- Certifications: "AWS Certified", "PMP", "Scrum Master"
- Methodologies: "Agile", "DevOps", "CI/CD"

EXAMPLES of what NOT to include:
- Soft skills: "communication", "teamwork", "leadership", "problem-solving"
- General terms: "experience", "knowledge", "ability", "skills"
- Job requirements: "bachelor's degree", "5+ years", "master's degree"
- Education majors: "Computer Science", "Engineering", "Business Administration"
- Vague terms: "strong", "excellent", "proficient", "familiar"
- Inferred technologies not explicitly mentioned

QUALITY OVER QUANTITY:
- Better to return 5 accurate keywords than 15 keywords with hallucinations
- Only extract what is genuinely present in the job description
- Do not try to reach a specific number of keywords

JOB DESCRIPTION:
{job_description}

Return only the JSON array of keywords that are explicitly mentioned in the job description:"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.llm_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Low temperature for more deterministic, factual extraction
            "max_tokens": 500    # Limit response length to prevent over-generation
        }
        
        try:
            logger.info("Making keyword analysis LLM API request", 
                       url=self.base_url, 
                       using_https=self.base_url.startswith('https://'))
            
            # Use httpx client with TLS enforcement
            async with create_httpx_client() as client:
                response = await client.post(self.base_url, headers=headers, json=data)
                
                logger.info("Keyword analysis LLM API response received",
                           status_code=response.status_code,
                           using_https=str(response.url).startswith('https://'),
                           content_length=len(response.content))
            
            # Handle specific HTTP status codes
            if response.status_code == 401:
                raise Exception("OpenRouter API authentication failed. Please check your OPENROUTER_API_KEY.")
            elif response.status_code == 403:
                raise Exception("OpenRouter API access forbidden. Please check your API key permissions.")
            elif response.status_code == 429:
                raise Exception("OpenRouter API rate limit exceeded. Please try again later.")
            
            response.raise_for_status()
            
            result = response.json()
            
            # Check for OpenRouter-specific error responses
            if "error" in result:
                error_msg = result["error"].get("message", "Unknown error")
                raise Exception(f"OpenRouter API error: {error_msg}")
            
            # Extract content from response
            if "choices" in result and len(result["choices"]) > 0:
                raw_content = result["choices"][0]["message"]["content"]
                logger.debug(f"Raw keyword analysis response: {raw_content}")
                
                # Parse JSON response
                try:
                    import json
                    # Clean the response to extract only JSON
                    cleaned_content = raw_content.strip()
                    
                    # Find JSON array in the response
                    start_idx = cleaned_content.find('[')
                    end_idx = cleaned_content.rfind(']')
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = cleaned_content[start_idx:end_idx+1]
                        keywords = json.loads(json_str)
                        
                        # Validate that it's a list of strings
                        if isinstance(keywords, list) and all(isinstance(k, str) for k in keywords):
                            logger.debug(f"Extracted {len(keywords)} keywords: {keywords}")
                            return keywords
                        else:
                            raise ValueError("Response is not a valid list of strings")
                    else:
                        raise ValueError("No JSON array found in response")
                        
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Failed to parse keyword analysis response as JSON: {e}")
                    logger.error(f"Raw response: {raw_content}")
                    # Fallback: try to extract keywords manually
                    return self._extract_keywords_fallback(raw_content)
                    
            else:
                raise Exception("No response content received from OpenRouter API")
            
        except httpx.ConnectError as e:
            if "SSL" in str(e) or "TLS" in str(e) or "certificate" in str(e).lower():
                logger.error(f"TLS connection error to OpenRouter API: {str(e)}")
                raise Exception(f"TLS connection failed to OpenRouter API. Please check your network configuration and SSL settings. Error: {str(e)}")
            else:
                logger.error(f"Connection error to OpenRouter API: {str(e)}")
                raise Exception(f"Failed to connect to OpenRouter API. Please check your network connection. Error: {str(e)}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception("OpenRouter API authentication failed. Please check your OPENROUTER_API_KEY.")
            else:
                logger.error(f"HTTP error to OpenRouter API: {e.response.status_code} - {str(e)}")
                raise Exception(f"OpenRouter API request failed: {e.response.status_code} - {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"Request error to OpenRouter API: {str(e)}")
            raise Exception(f"OpenRouter API request failed: {str(e)}")
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error to OpenRouter API: {str(e)}")
            raise Exception(f"OpenRouter API request timed out. Please try again later. Error: {str(e)}")
        except ssl.SSLError as e:
            logger.error(f"SSL error when connecting to OpenRouter API: {str(e)}")
            raise Exception(f"SSL certificate verification failed for OpenRouter API. Error: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected response format from OpenRouter API: {str(e)}")
    
    def _extract_keywords_fallback(self, raw_content: str) -> list[str]:
        """
        Fallback method to extract keywords when JSON parsing fails
        """
        import re
        
        # Try to find quoted strings that look like technical terms
        keywords = []
        
        # Look for quoted strings
        quoted_pattern = r'"([^"]+)"'
        matches = re.findall(quoted_pattern, raw_content)
        
        for match in matches:
            # Filter for technical-looking terms
            if len(match) > 1 and not match.lower() in ['and', 'or', 'the', 'a', 'an', 'to', 'for', 'with', 'in', 'on', 'at']:
                keywords.append(match)
        
        # If no quoted strings, try to extract capitalized words
        if not keywords:
            cap_pattern = r'\b[A-Z][a-zA-Z0-9+#\.]*\b'
            matches = re.findall(cap_pattern, raw_content)
            keywords = [m for m in matches if len(m) > 2][:20]
        
        return keywords[:20]  # Limit to 20 keywords
    
    def _format_applicant_data(self, applicant_data: Dict[str, Any]) -> str:
        """Format applicant data in Markdown format for better LLM parsing"""
        
        formatted_data = []
        
        # Personal Information
        if applicant_data.get("personal_info"):
            personal = applicant_data["personal_info"]
            formatted_data.append("# Personal Information")
            formatted_data.append("")
            formatted_data.append(f"**Name:** {personal.get('name', 'N/A')}")
            formatted_data.append(f"**Email:** {personal.get('email', 'N/A')}")
            formatted_data.append(f"**Phone:** {personal.get('phone', 'N/A')}")
            formatted_data.append(f"**Location:** {personal.get('location', 'N/A')}")
            if personal.get('summary'):
                formatted_data.append(f"**Professional Summary:** {personal['summary']}")
            formatted_data.append("")
        
        # Education
        if applicant_data.get("education"):
            formatted_data.append("# Education")
            formatted_data.append("")
            for edu in applicant_data["education"]:
                formatted_data.append(f"## {edu.get('degree', 'N/A')} in {edu.get('field_of_study', 'N/A')}")
                formatted_data.append(f"**Institution:** {edu.get('institution', 'N/A')}")
                formatted_data.append(f"**Location:** {edu.get('location', 'N/A')}")
                formatted_data.append(f"**Graduation Date:** {edu.get('end_date', 'N/A')}")
                if edu.get('gpa'):
                    # Format GPA with 2 decimal places if it's a number
                    gpa_value = edu['gpa']
                    try:
                        # Try to format as a number with 2 decimal places
                        gpa_formatted = f"{float(gpa_value):.2f}"
                        formatted_data.append(f"**GPA:** {gpa_formatted}")
                    except (ValueError, TypeError):
                        # If it's not a number (e.g., "First Class"), use as-is
                        formatted_data.append(f"**GPA:** {gpa_value}")
                formatted_data.append("")
        
        # Work Experience
        if applicant_data.get("experiences"):
            formatted_data.append("# Work Experience")
            formatted_data.append("")
            for exp in applicant_data["experiences"]:
                formatted_data.append(f"## {exp.get('company', 'N/A')}")
                formatted_data.append(f"**Location:** {exp.get('location', 'N/A')}")
                formatted_data.append(f"**Duration:** {exp.get('start_date', 'N/A')} - {'Present' if exp.get('is_current') else exp.get('end_date', 'N/A')}")
                
                # Job Titles
                if exp.get('titles'):
                    formatted_data.append("**Positions:**")
                    for title in exp['titles']:
                        primary_indicator = " *(Primary)*" if title.get('is_primary') else ""
                        formatted_data.append(f"- {title.get('title', 'N/A')}{primary_indicator}")
                
                if exp.get('description'):
                    formatted_data.append("**Description:**")
                    formatted_data.append(f"{exp['description']}")
                
                formatted_data.append("")
        
        # Projects
        if applicant_data.get("projects"):
            formatted_data.append("# Projects")
            formatted_data.append("")
            for project in applicant_data["projects"]:
                formatted_data.append(f"## {project.get('name', 'N/A')}")
                formatted_data.append(f"**Duration:** {project.get('start_date', 'N/A')} - {'Present' if project.get('is_current') else project.get('end_date', 'N/A')}")
                if project.get('url'):
                    formatted_data.append(f"**URL:** {project['url']}")
                if project.get('description'):
                    formatted_data.append("**Description:**")
                    formatted_data.append(f"{project['description']}")
                
                # Technologies Used
                if project.get('technologies_used'):
                    formatted_data.append("**Technologies Used:**")
                    formatted_data.append(f"{project['technologies_used']}")
                
                formatted_data.append("")
        
        # Skills
        if applicant_data.get("skills"):
            formatted_data.append("# Skills")
            formatted_data.append("")
            skill_names = [skill.get('name', 'N/A') for skill in applicant_data["skills"]]
            # Group skills in a more readable format
            skills_per_line = 8
            for i in range(0, len(skill_names), skills_per_line):
                skill_group = skill_names[i:i + skills_per_line]
                formatted_data.append(f"- {' • '.join(skill_group)}")
            formatted_data.append("")
        
        # Certifications
        if applicant_data.get("certifications"):
            formatted_data.append("# Certifications")
            formatted_data.append("")
            for cert in applicant_data["certifications"]:
                formatted_data.append(f"## {cert.get('name', 'N/A')}")
                formatted_data.append(f"**Issuer:** {cert.get('issuer', 'N/A')}")
                formatted_data.append(f"**Issue Date:** {cert.get('issue_date', 'N/A')}")
                if cert.get('expiry_date'):
                    formatted_data.append(f"**Expiry Date:** {cert['expiry_date']}")
                formatted_data.append("")
        
        # Publications
        if applicant_data.get("publications"):
            formatted_data.append("# Publications")
            formatted_data.append("")
            for pub in applicant_data["publications"]:
                formatted_data.append(f"## {pub.get('title', 'N/A')}")
                if pub.get('co_authors'):
                    formatted_data.append(f"**Co-authors:** {pub['co_authors']}")
                if pub.get('publisher'):
                    formatted_data.append(f"**Publisher:** {pub['publisher']}")
                if pub.get('publication_date'):
                    formatted_data.append(f"**Publication Date:** {pub['publication_date']}")
                if pub.get('url'):
                    formatted_data.append(f"**URL:** {pub['url']}")
                formatted_data.append("")
        
        # Websites
        if applicant_data.get("websites"):
            formatted_data.append("# Websites & Links")
            formatted_data.append("")
            for website in applicant_data["websites"]:
                formatted_data.append(f"- **{website.get('site_name', 'N/A')}:** {website.get('url', 'N/A')}")
            formatted_data.append("")
        
        return "\n".join(formatted_data)


# Create singleton instance
llm_service = LLMService()
