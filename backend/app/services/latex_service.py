"""
LaTeX resume generation service
"""
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Template
import logging

logger = logging.getLogger(__name__)

class LaTeXService:
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.template_path = self.template_dir / "ResumeTemplate1.tex"
        
    def generate_optimized_resume_pdf(self, resume_data: Dict[str, Any]) -> bytes:
        """
        Generate an AI-optimized PDF resume from structured data using LLM and LaTeX
        
        Args:
            resume_data: Dictionary containing resume information and job description
            
        Returns:
            PDF content as bytes
            
        Raises:
            LaTeXCompilationError: If LaTeX compilation fails
        """
        try:
            # Create temporary directory for LaTeX compilation
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Generate optimized LaTeX content using LLM
                latex_content = self._generate_optimized_latex(resume_data)
                
                # Write LaTeX file
                tex_file = temp_path / "resume.tex"
                tex_file.write_text(latex_content, encoding='utf-8')
                
                # Compile LaTeX to PDF
                pdf_file = self._compile_latex(tex_file, temp_path)
                
                # Read PDF content
                return pdf_file.read_bytes()
                
        except Exception as e:
            logger.error(f"Failed to generate optimized resume PDF: {str(e)}")
            raise LaTeXCompilationError(f"Failed to generate optimized resume PDF: {str(e)}")

    def generate_resume_pdf(self, resume_data: Dict[str, Any]) -> bytes:
        """
        Generate a PDF resume from structured data using LaTeX
        
        Args:
            resume_data: Dictionary containing resume information
            
        Returns:
            PDF content as bytes
            
        Raises:
            LaTeXCompilationError: If LaTeX compilation fails
        """
        try:
            # Create temporary directory for LaTeX compilation
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Load and render LaTeX template
                latex_content = self._render_template(resume_data)
                
                # Write LaTeX file
                tex_file = temp_path / "resume.tex"
                tex_file.write_text(latex_content, encoding='utf-8')
                
                # Compile LaTeX to PDF
                pdf_file = self._compile_latex(tex_file, temp_path)
                
                # Read PDF content
                return pdf_file.read_bytes()
                
        except Exception as e:
            logger.error(f"Failed to generate resume PDF: {str(e)}")
            raise LaTeXCompilationError(f"Failed to generate resume PDF: {str(e)}")
    
    def _generate_optimized_latex(self, data: Dict[str, Any]) -> str:
        """Generate optimized LaTeX content using LLM"""
        try:
            # For now, use the template-based approach
            # TODO: Integrate with actual LLM service (OpenAI, Anthropic, etc.)
            template_content = self.template_path.read_text(encoding='utf-8')
            template = Template(template_content)
            
            # Add job description to data for template processing
            optimized_data = data.copy()
            optimized_data['job_description'] = data.get('job_description', '')
            
            # Debug: Log the data being passed to template
            logger.info(f"Template data: {optimized_data}")
            
            rendered_content = template.render(**optimized_data)
            
            # Debug: Log the rendered content
            logger.info(f"Rendered LaTeX content: {rendered_content[:500]}...")
            
            return rendered_content
        except Exception as e:
            logger.error(f"Failed to generate optimized LaTeX: {str(e)}")
            raise LaTeXCompilationError(f"LLM optimization failed: {str(e)}")

    def _render_template(self, data: Dict[str, Any]) -> str:
        """Render LaTeX template with data"""
        try:
            template_content = self.template_path.read_text(encoding='utf-8')
            template = Template(template_content)
            return template.render(**data)
        except Exception as e:
            logger.error(f"Failed to render template: {str(e)}")
            raise LaTeXCompilationError(f"Template rendering failed: {str(e)}")
    
    def _compile_latex(self, tex_file: Path, output_dir: Path) -> Path:
        """Compile LaTeX file to PDF"""
        try:
            # Run pdflatex
            result = subprocess.run([
                'pdflatex',
                '-interaction=nonstopmode',
                '-output-directory', str(output_dir),
                str(tex_file)
            ], capture_output=True, text=True, timeout=30)
            
            # Log the full output for debugging
            logger.debug(f"LaTeX stdout: {result.stdout}")
            logger.debug(f"LaTeX stderr: {result.stderr}")
            logger.debug(f"LaTeX return code: {result.returncode}")
            
            if result.returncode != 0:
                error_msg = f"LaTeX compilation failed (return code {result.returncode}): {result.stderr or result.stdout}"
                logger.error(error_msg)
                raise LaTeXCompilationError(error_msg)
            
            # Return PDF file path (PDF has same name as input file)
            pdf_file = output_dir / f"{tex_file.stem}.pdf"
            if not pdf_file.exists():
                logger.error(f"PDF file was not generated at {pdf_file}")
                raise LaTeXCompilationError("PDF file was not generated")
            
            logger.debug(f"PDF file found at {pdf_file}, size: {pdf_file.stat().st_size} bytes")
            return pdf_file
            
        except subprocess.TimeoutExpired:
            raise LaTeXCompilationError("LaTeX compilation timed out")
        except FileNotFoundError:
            raise LaTeXCompilationError("pdflatex not found. Please install LaTeX distribution.")
        except Exception as e:
            logger.error(f"LaTeX compilation error: {str(e)}")
            raise LaTeXCompilationError(f"LaTeX compilation error: {str(e)}")

class LaTeXCompilationError(Exception):
    """Raised when LaTeX compilation fails"""
    pass

# Global instance
latex_service = LaTeXService()
