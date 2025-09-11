"""
LLM Service for resume generation
"""

import os
import requests
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY") or settings.OPENROUTER_API_KEY
        self.llm_model = os.getenv("OPENROUTER_LLM_MODEL") or settings.OPENROUTER_LLM_MODEL or "anthropic/claude-3.5-sonnet"
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Debug logging
        if not self.api_key:
            print("WARNING: OPENROUTER_API_KEY is not set!")
        else:
            print(f"OpenRouter API key loaded: {self.api_key[:10]}...")
        print(f"Using LLM model: {self.llm_model}")
    
    async def generate_resume(
        self, 
        job_title: str,
        job_description: str,
        applicant_data: Dict[str, Any],
        template_content: str
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
- Use X,Y,Z format for achievements
- Do NOT add explanations, comments, or markdown formatting
- Return ONLY valid LaTeX code starting with \\begin{{document}} and ending with \\end{{document}}

ACCURACY REQUIREMENTS:
1. Use ONLY knowledge found from the applicant's history:
   - Skills section must contain ONLY skills present in the applicant's skills list
   - Experience section must NOT claim achievements the applicant has not claimed
   - Experience section must use ONLY skills found in the applicant's skills
   - Experience section must display the location of the every experience, even if Remote
   - Certifications section must use EXACT naming from the applicant's certifications

2. Education:
   - Use the end date as provided by the applicant
   - Include the word "Expected" if provided by the applicant
   - Include the month and year for the end date
   - Do not leave the end date empty
   - Do not display "Current", "In Progress", or "N/A" for the end date of any education
   - Do not display the location for education

3. Project dates:
   - Do NOT show any dates for projects
   - Use a blank space ' ' for the date parameter
   
4. Avoid vague adjectives - use only hard truths and specific facts


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
            response = requests.post(self.base_url, headers=headers, json=data, timeout=60)
            
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
            
        except requests.exceptions.RequestException as e:
            if "401" in str(e):
                raise Exception("OpenRouter API authentication failed. Please check your OPENROUTER_API_KEY.")
            else:
                raise Exception(f"OpenRouter API request failed: {str(e)}")
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
    
    def _format_applicant_data(self, applicant_data: Dict[str, Any]) -> str:
        """Format applicant data for the LLM prompt"""
        
        formatted_data = []
        
        # Personal Information
        if applicant_data.get("personal_info"):
            personal = applicant_data["personal_info"]
            formatted_data.append("PERSONAL INFORMATION:")
            formatted_data.append(f"Name: {personal.get('name', 'N/A')}")
            formatted_data.append(f"Email: {personal.get('email', 'N/A')}")
            formatted_data.append(f"Phone: {personal.get('phone', 'N/A')}")
            formatted_data.append(f"Location: {personal.get('location', 'N/A')}")
            if personal.get('summary'):
                formatted_data.append(f"Professional Summary: {personal['summary']}")
            formatted_data.append("")
        
        # Education
        if applicant_data.get("education"):
            formatted_data.append("EDUCATION:")
            for edu in applicant_data["education"]:
                formatted_data.append(f"- {edu.get('degree', 'N/A')} in {edu.get('field_of_study', 'N/A')}")
                formatted_data.append(f"  Institution: {edu.get('institution', 'N/A')}")
                formatted_data.append(f"  Location: {edu.get('location', 'N/A')}")
                formatted_data.append(f"  Graduation Date: {edu.get('graduation_date', 'N/A')}")
                if edu.get('gpa'):
                    formatted_data.append(f"  GPA: {edu['gpa']}")
                formatted_data.append("")
        
        # Work Experience
        if applicant_data.get("experiences"):
            formatted_data.append("WORK EXPERIENCE:")
            for exp in applicant_data["experiences"]:
                formatted_data.append(f"- Company: {exp.get('company', 'N/A')}")
                formatted_data.append(f"  Location: {exp.get('location', 'N/A')}")
                formatted_data.append(f"  Start Date: {exp.get('start_date', 'N/A')}")
                formatted_data.append(f"  End Date: {'Present' if exp.get('is_current') else exp.get('end_date', 'N/A')}")
                
                # Job Titles
                if exp.get('titles'):
                    formatted_data.append("  Job Titles:")
                    for title in exp['titles']:
                        primary_indicator = " (Primary)" if title.get('is_primary') else ""
                        formatted_data.append(f"    - {title.get('title', 'N/A')}{primary_indicator}")
                
                if exp.get('description'):
                    formatted_data.append(f"  Description: {exp['description']}")
                
                # Achievements
                if exp.get('achievements'):
                    formatted_data.append("  Key Achievements:")
                    for achievement in exp['achievements']:
                        formatted_data.append(f"    - {achievement.get('description', 'N/A')}")
                
                formatted_data.append("")
        
        # Projects
        if applicant_data.get("projects"):
            formatted_data.append("PROJECTS:")
            for project in applicant_data["projects"]:
                formatted_data.append(f"- Project: {project.get('name', 'N/A')}")
                formatted_data.append(f"  Start Date: {project.get('start_date', 'N/A')}")
                formatted_data.append(f"  End Date: {'Present' if project.get('is_current') else project.get('end_date', 'N/A')}")
                if project.get('url'):
                    formatted_data.append(f"  URL: {project['url']}")
                if project.get('description'):
                    formatted_data.append(f"  Description: {project['description']}")
                
                # Technologies
                if project.get('technologies'):
                    formatted_data.append("  Technologies Used:")
                    for tech in project['technologies']:
                        formatted_data.append(f"    - {tech.get('technology', 'N/A')}")
                
                # Achievements
                if project.get('achievements'):
                    formatted_data.append("  Key Achievements:")
                    for achievement in project['achievements']:
                        formatted_data.append(f"    - {achievement.get('description', 'N/A')}")
                
                formatted_data.append("")
        
        # Skills
        if applicant_data.get("skills"):
            formatted_data.append("SKILLS:")
            for skill in applicant_data["skills"]:
                formatted_data.append(f"- {skill.get('name', 'N/A')}")
            formatted_data.append("")
        
        # Certifications
        if applicant_data.get("certifications"):
            formatted_data.append("CERTIFICATIONS:")
            for cert in applicant_data["certifications"]:
                formatted_data.append(f"- {cert.get('name', 'N/A')}")
                formatted_data.append(f"  Issuer: {cert.get('issuer', 'N/A')}")
                formatted_data.append(f"  Issue Date: {cert.get('issue_date', 'N/A')}")
                if cert.get('expiry_date'):
                    formatted_data.append(f"  Expiry Date: {cert['expiry_date']}")
                formatted_data.append("")
        
        # Publications
        if applicant_data.get("publications"):
            formatted_data.append("PUBLICATIONS:")
            for pub in applicant_data["publications"]:
                formatted_data.append(f"- {pub.get('title', 'N/A')}")
                if pub.get('co_authors'):
                    formatted_data.append(f"  Co-authors: {pub['co_authors']}")
                if pub.get('publisher'):
                    formatted_data.append(f"  Publisher: {pub['publisher']}")
                if pub.get('publication_date'):
                    formatted_data.append(f"  Publication Date: {pub['publication_date']}")
                if pub.get('url'):
                    formatted_data.append(f"  URL: {pub['url']}")
                formatted_data.append("")
        
        # Websites
        if applicant_data.get("websites"):
            formatted_data.append("WEBSITES:")
            for website in applicant_data["websites"]:
                formatted_data.append(f"- {website.get('site_name', 'N/A')}: {website.get('url', 'N/A')}")
            formatted_data.append("")
        
        return "\n".join(formatted_data)


# Create singleton instance
llm_service = LLMService()
