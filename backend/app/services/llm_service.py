"""
LLM Service for resume generation
"""

import httpx
import ssl
import tempfile
import subprocess
import re
import json
import PyPDF2
from pathlib import Path
from typing import Dict, Any, Tuple
from app.core.settings import settings
from app.utils.tls_utils import create_httpx_client, validate_tls_configuration
from app.services.latex_service import latex_service, LaTeXCompilationError
from app.utils.template_utils import combine_with_template_preamble
from app.utils.latex_sanitizer import sanitize_latex, LaTeXSecurityError

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
    
        
    async def _generate_initial_resume(
        self,
        job_title: str,
        job_description: str,
        applicant_knowledge: str,
        template_content: str,
        locale: str
    ) -> str:
        """
        Generate the initial resume draft
        """
        prompt = f"""You are an expert resume optimizer. Your task is to generate a one-page resume in LaTeX format tailored to a specific job description. Follow these stages carefully and use your reasoning from each stage to inform the next.

---

### Stage 1: Keyword Extraction  
Analyze the job description below and extract the most important keywords, skills, and responsibilities. Focus on technical terms, tools, certifications, and role-specific verbs.

### JOB DESCRIPTION START
{job_description}
### JOB DESCRIPTION END

---

### Stage 2: Applicant Strengths Analysis  
Given the applicant's background below, identify which skills, experiences, and projects are most relevant to the job description.  
- Highlight the most aligned experiences and projects  
- Identify which education details are relevant  
- List any skills or content that should be excluded to keep the resume concise and targeted  
- Do not fabricate or infer accomplishments not present in the applicant's history

### APPLICANT BACKGROUND START
{applicant_knowledge}
### APPLICANT BACKGROUND END

---

### Stage 3: Resume Construction  
Using your analysis from Stage 1 and Stage 2, generate a one-page resume in LaTeX format using the provided template.  
- Use the XYZ format for bullet points: *Achieved X by doing Y with Z*  
- Group skills logically by category (e.g., Programming Languages, Frameworks, Tools, etc.) and ensure each skill is placed in the most appropriate category.
- Limit each experience to a maximum of 4 relevant bullet points  
- Format phone numbers according to the specified locale: **{locale}**  
- Resume must fit within a single LaTeX page. If necessary, truncate less relevant bullets or sections. Do not exceed 1,000 words or 60 lines of LaTeX code  
- If no direct match is found for a keyword or requirement, omit or generalize the bullet point while preserving factual accuracy  
- Do NOT include any dates for projects in the `\\resumeProjectHeading` command. Use empty braces {{}} for project dates.
- Ensure formatting matches the LaTeX template below

### LATEX TEMPLATE START
{template_content}
### LATEX TEMPLATE END

---

### Final Output Requirements

Return **only** valid LaTeX code that:
- Starts with `\\begin{{document}}` and ends with `\\end{{document}}`
- Includes no commentary, reasoning, or explanation
- Fits on **one page only**
- Uses only content found in the applicant's history

---

## ✅ Accuracy Requirements

### 1. Use ONLY knowledge found from the applicant's history
- **Skills section** must contain ONLY skills present in the applicant's skills list  
- **Experience section** must NOT claim accomplishments the applicant has not claimed  
- **Experience section** must use ONLY skills found in the applicant's skills  
- **Certifications section** must use EXACT naming from the applicant's certifications  

### 2. Education
- **GPA FORMATTING**: If GPA is a number, display it with exactly 2 decimal places (e.g., "3.85", "4.00"). If GPA is text (e.g., "First Class", "Magna Cum Laude"), display as-is.

### 3. Experience
- **MANDATORY**: Display the location of every experience, even if Remote  
- **MANDATORY**: Choose the most relevant title per experience or join titles with `/` if relevant  
- **EXPERIENCE FORMATTING**: Use `\\resumeSubheading` for the most recent role at each company, and `\\resumeSubSubheading` for any previous roles at the same company.

### 4. Section Organization and Ordering
- **CRITICAL**: Analyze the job description and applicant's background to determine the optimal section order  
- **STRATEGIC PLACEMENT**: Place sections with the strongest keyword matches and most relevant content near the top (after header)  
- **REASONING REQUIRED**: Consider which sections will best attract recruiter attention for this specific role  
- **COMMON PATTERNS**:
  - For technical roles: Skills → Experience → Projects → Education → Certifications  
  - For experienced professionals: Experience → Skills → Projects → Education → Certifications  
  - For recent graduates: Education → Skills → Projects → Experience → Certifications  
  - For career changers: Skills → Projects → Experience → Education → Certifications  
- **FLEXIBILITY**: Adapt the order based on what will showcase the applicant's fit for the role most effectively  
- **KEYWORD PRIORITY**: Sections containing the most job-relevant keywords should appear earlier"""

        return await self._make_llm_request(prompt)
    
    async def _verify_and_correct_resume(
        self,
        initial_resume: str,
        applicant_knowledge: str,
        job_title: str,
        job_description: str,
        page_count: int = None
    ) -> str:
        """
        Verify the initial resume against applicant data and correct any inaccuracies
        Also optimize for length if the resume is longer than one page
        """
        
        # Add length optimization instructions if needed
        length_instruction = ""
        logger.debug(f"Verification method received page_count: {page_count} (type: {type(page_count)})")
        if page_count and page_count > 1:
            logger.info(f"Resume is {page_count} pages long - adding length optimization instructions")
            length_instruction = f"""

## CRITICAL: Length Optimization Required
The current resume is {page_count} pages long. You MUST reduce it to exactly 1 page by:
- Selecting only the most relevant experiences (max 3)
- Limiting bullet points to maximum of 4 per experience
- Including only the most relevant projects (max 3)
- Prioritizing recent and job-relevant content
- Removing less critical details while maintaining impact
- Focus on quantified achievements and direct keyword matches
- Keep only the strongest, most relevant accomplishments

**PRIORITY ORDER for content selection:**
1. Most recent experience (last 3-5 years)
2. Direct keyword matches with job description
3. Quantified achievements with measurable impact
4. Technical skills explicitly mentioned in job posting
5. Leadership roles and notable accomplishments

**CONTENT LIMITS:**
- Maximum 3 work experiences
- Maximum 4 bullet points per experience
- Maximum 3 projects
- Concise skills section with job-relevant skills only
- Brief education section (include GPA only if >3.5)
"""
        
        prompt = f"""# Resume Fact-Checking and Optimization Task

You are a fact-checking expert reviewing a resume for accuracy and length optimization. Your task is to compare the generated resume against the applicant's actual data, correct any inaccuracies, and ensure it fits on one page.

## Critical Task
- Review the generated resume line by line
- Compare every statement against the applicant's actual data
- Identify and correct any false, exaggerated, or hallucinated information
- Ensure all skills, experiences, achievements, and details are factually accurate
- Maintain the LaTeX formatting and structure
- Return ONLY the corrected LaTeX code

## Verification Rules

### 1. Skills Verification
- Remove any skills NOT explicitly listed in the applicant's skills section
- Do NOT add skills that are implied but not stated
- Do NOT add skills mentioned in job descriptions but not in applicant data
- **Cross-reference**: Every skill must appear in the applicant's actual skills list

### 2. Experience Verification
- Remove any accomplishments or achievements NOT claimed by the applicant
- Do NOT embellish or exaggerate existing accomplishments
- Do NOT add quantified results unless explicitly provided by the applicant
- Ensure all job responsibilities match what the applicant actually described
- **Fact-check**: Compare each bullet point against the applicant's actual experience descriptions

### 3. Education Verification
- Use EXACT graduation dates, GPAs, and details as provided
- Do NOT modify or improve upon the applicant's educational achievements
- Remove any honors, awards, or distinctions not mentioned by the applicant
- **Accuracy check**: Verify every educational detail matches the source data exactly

### 4. Project Verification
- Ensure project descriptions match the applicant's actual descriptions
- Remove any technologies or achievements not mentioned by the applicant
- Do NOT enhance or embellish project outcomes
- **Technology check**: Only include technologies explicitly listed in the applicant's project data
- **Achievement check**: Only include accomplishments explicitly stated by the applicant
- **Date formatting**: Ensure project dates use empty braces {{}} not {{' '}} or {{""}} or quoted spaces

### 5. General Accuracy
- Remove vague adjectives or superlatives not supported by facts
- Ensure all dates, locations, and company names are accurate
- Remove any industry buzzwords not used by the applicant
- **Consistency check**: Verify all factual details match the source data

{length_instruction}

## Applicant's Actual Data
{applicant_knowledge}

## Job Description (for context only - do NOT add information from here)
```
{job_description}
```

## Generated Resume to Verify
```latex
{initial_resume}
```

Please return the corrected resume with all inaccuracies removed, maintaining the LaTeX format."""

        return await self._make_llm_request(prompt)
    
    def _clean_latex_content(self, latex_content: str) -> str:
        """
        Clean up common LaTeX formatting issues in the generated resume
        """
        logger.debug("Cleaning LaTeX content for formatting issues")
           
        # Remove bolding from skills section only (but keep category headers bolded)
        # Find the skills section and remove \textbf{} wrapping from individual skills after colons
        skills_section_pattern = r'(\\section\{[^}]*[Ss]kills[^}]*\}.*?)(?=\\section|\Z)'
        
        def clean_skills_section(match):
            skills_content = match.group(1)
            # Remove \textbf{} wrapping from skills AFTER the colon, but keep category headers bolded
            # Pattern matches: }{: \textbf{skill} and removes the \textbf{} wrapper
            skills_content = re.sub(r'(\}\{\:\s*)\\textbf\{([^}]+)\}', r'\1\2', skills_content)
            # Also remove Markdown-style bolding **text** after colons
            skills_content = re.sub(r'(\}\{\:\s*)\*\*([^*]+)\*\*', r'\1\2', skills_content)
            return skills_content
        
        latex_content = re.sub(skills_section_pattern, clean_skills_section, latex_content, flags=re.DOTALL)
        
        # Convert any remaining Markdown-style bolding **text** to LaTeX \textbf{text} in the entire document
        # This handles cases where the LLM used Markdown formatting instead of LaTeX
        latex_content = re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', latex_content)
        
        logger.debug(f"LaTeX content cleaned, length: {len(latex_content)}")
        return latex_content
    
    async def _make_llm_request(self, prompt: str) -> str:
        """
        Make a request to the LLM API and return the cleaned response
        """
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
    
    def _estimate_pages_from_content(self, latex_content: str) -> int:
        """
        Estimate page count based on LaTeX content analysis
        """
        # Count different types of content
        resume_items = latex_content.count('\\resumeItem{')
        resume_subheadings = latex_content.count('\\resumeSubheading')
        resume_projects = latex_content.count('\\resumeProjectHeading')
        
        # Estimate based on content density
        # Typical resume: ~15-20 items per page
        # Each subheading (job) takes ~3-4 lines
        # Each project takes ~2-3 lines
        
        total_content_items = resume_items + (resume_subheadings * 3) + (resume_projects * 2)
        
        # Rough estimation: 15-20 content items per page
        estimated_pages = max(1, round(total_content_items / 17))
        
        # Also consider character count as backup
        char_based_pages = max(1, round(len(latex_content) / 2500))
        
        # Use the higher estimate to be conservative
        final_estimate = max(estimated_pages, char_based_pages)
        
        logger.debug(f"Content analysis: {resume_items} items, {resume_subheadings} jobs, {resume_projects} projects")
        logger.debug(f"Estimated pages: {final_estimate} (content-based: {estimated_pages}, char-based: {char_based_pages})")
        
        return final_estimate
    
    async def _compile_latex_and_count_pages(self, latex_content: str) -> Tuple[int, str]:
        """
        Compile LaTeX content to PDF and return page count using the existing LaTeXService
        Returns: (page_count, error_message)
        """
        logger.debug("Starting LaTeX compilation for page count")
        logger.debug(f"LaTeX content length: {len(latex_content)} characters")
        
        # Import required modules
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                tex_file = temp_path / "resume.tex"
                
                # Combine template preamble with content (same as user-facing compilation)
                complete_latex = combine_with_template_preamble(latex_content, "ResumeTemplate1.tex")
                
                logger.debug(f"Complete LaTeX length: {len(complete_latex)} characters")
                
                # Write complete LaTeX content to temporary file
                with open(tex_file, 'w', encoding='utf-8') as f:
                    f.write(complete_latex)
                
                # Use the existing LaTeXService for compilation (same as user-facing PDF generation)
                pdf_file = latex_service.compile_latex(tex_file, temp_path)
                
                logger.debug(f"LaTeX compilation successful, PDF created at: {pdf_file}")
                
                # Count pages using PyPDF2 (more reliable than pdfinfo)
                try:
                    with open(pdf_file, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        page_count = len(pdf_reader.pages)
                        logger.info(f"LaTeX compilation successful: {page_count} pages")
                        return page_count, ""
                        
                except ImportError:
                    logger.warning("PyPDF2 not available, trying pdfinfo")
                    # Fallback to pdfinfo if PyPDF2 is not available
                    try:
                        result = subprocess.run([
                            'pdfinfo', str(pdf_file)
                        ], capture_output=True, text=True, timeout=10)
                        
                        if result.returncode == 0:
                            # Extract page count from pdfinfo output
                            for line in result.stdout.split('\n'):
                                if line.startswith('Pages:'):
                                    page_count = int(line.split(':')[1].strip())
                                    logger.info(f"LaTeX compilation successful: {page_count} pages")
                                    return page_count, ""
                        
                        # Fallback: try to count pages using file size estimation
                        file_size = pdf_file.stat().st_size
                        # Very rough estimation: typical single page is 20-50KB
                        estimated_pages = max(1, round(file_size / 35000))
                        logger.warning(f"Using file size estimation: {estimated_pages} pages (file size: {file_size} bytes)")
                        return estimated_pages, "Used file size estimation"
                        
                    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError) as e:
                        logger.warning(f"pdfinfo failed, using file size estimation: {e}")
                        # Final fallback: use content-based estimation
                        estimated_pages = self._estimate_pages_from_content(latex_content)
                        logger.warning(f"Using content-based estimation: {estimated_pages} pages")
                        return estimated_pages, f"Used content estimation due to: {str(e)}"
                        
                except Exception as e:
                    logger.warning(f"PyPDF2 failed, using content estimation: {e}")
                    # Final fallback: use content-based estimation
                    estimated_pages = self._estimate_pages_from_content(latex_content)
                    logger.warning(f"Using content-based estimation: {estimated_pages} pages")
                    return estimated_pages, f"Used content estimation due to: {str(e)}"
                
        except LaTeXCompilationError as e:
            logger.warning(f"LaTeX compilation failed: {e}")
            # Use content-based estimation instead of defaulting to 1 page
            estimated_pages = self._estimate_pages_from_content(latex_content)
            logger.warning(f"Using content-based estimation: {estimated_pages} pages")
            return estimated_pages, f"LaTeX compilation failed: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during LaTeX compilation: {e}")
            # Fallback: use content-based estimation
            estimated_pages = self._estimate_pages_from_content(latex_content)
            logger.warning(f"Using content-based estimation: {estimated_pages} pages")
            return estimated_pages, f"Unexpected error, using estimation: {str(e)}"
    
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
            formatted_data.append("# Education (Include only the most relevant education and GPA if it's strong (>3.5)):")
            formatted_data.append("")
            for edu in applicant_data["education"]:
                formatted_data.append(f"## {edu.get('degree', 'N/A')} in {edu.get('field_of_study', 'N/A')}")
                formatted_data.append(f"**Institution:** {edu.get('institution', 'N/A')}")
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
            formatted_data.append("# Professional Experience")
            formatted_data.append("")
            for exp in applicant_data["experiences"]:
                formatted_data.append(f"## {exp.get('company', '')}")
                formatted_data.append(f"**Location:** {exp.get('location', '')}")
                formatted_data.append(f"**Duration:** {exp.get('start_date', '')} - {'Present' if exp.get('is_current') else exp.get('end_date', '')}")
                
                # Job Titles
                if exp.get('titles'):
                    formatted_data.append("**Position titles (You can pick the most relevant title or combine titles if needed):**")
                    for title in exp['titles']:
                        primary_indicator = " *(Primary)*" if title.get('is_primary') and len(exp['titles']) > 1 else ""
                        formatted_data.append(f"- {title.get('title', 'N/A')}{primary_indicator}")
                
                if exp.get('description'):
                    formatted_data.append(f"**Description:** {exp['description']}")
                
                formatted_data.append("")
        
        # Projects
        if applicant_data.get("projects"):
            formatted_data.append("# Projects")
            formatted_data.append("")
            for project in applicant_data["projects"]:
                formatted_data.append(f"## {project.get('name', '')}")
                if project.get('role'):
                    formatted_data.append(f"**Role:** {project['role']}")
                # Do not display the duration for projects
                if project.get('url'):
                    formatted_data.append(f"**URL:** {project['url']}")
                if project.get('description'):
                    formatted_data.append(f"**Description:** {project['description']}")
                
                # Technologies Used
                if project.get('technologies_used'):
                    formatted_data.append(f"**Technologies Used:** {project['technologies_used']}")
                
                formatted_data.append("")
        
        # Skills
        if applicant_data.get("skills"):
            formatted_data.append("# Skills (Group skills logically by category - Programming Languages, Frameworks, Tools, etc. - and ensure each skill is placed in the most appropriate category):")
            skill_names = [skill.get('name', '') for skill in applicant_data["skills"]]
            formatted_data.append(", ".join(skill_names))
            formatted_data.append("")
        
        # Certifications
        if applicant_data.get("certifications"):
            formatted_data.append("# Certifications (Include only the most relevant certifications):")
            formatted_data.append("")
            for cert in applicant_data["certifications"]:
                formatted_data.append(f"## {cert.get('name', '')}")
                formatted_data.append(f"**Issuer:** {cert.get('issuer', '')}")
                formatted_data.append("")
        
        # Publications
        if applicant_data.get("publications"):
            formatted_data.append("# Publications (Include only the most relevant publications):")
            formatted_data.append("")
            for pub in applicant_data["publications"]:
                formatted_data.append(f"## {pub.get('title', '')}")
                if pub.get('authors'):
                    formatted_data.append(f"**Author(s):** {pub['authors']}")
                if pub.get('publisher'):
                    formatted_data.append(f"**Publisher:** {pub['publisher']}")
                if pub.get('publication_date'):
                    formatted_data.append(f"**Publication Date:** {pub['publication_date']}")
                if pub.get('url'):
                    formatted_data.append(f"**URL:** {pub['url']}")
                formatted_data.append("")
        
        # Websites
        if applicant_data.get("websites"):
            formatted_data.append("# Websites & Links (Include only the most relevant websites and links):")
            formatted_data.append("")
            for website in applicant_data["websites"]:
                formatted_data.append(f"- **{website.get('site_name', 'N/A')}:** {website.get('url', 'N/A')}")
            formatted_data.append("")
        
        return "\n".join(formatted_data)


# Create singleton instance
llm_service = LLMService()
