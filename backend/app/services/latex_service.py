"""
LaTeX resume generation service
"""
import subprocess
import tempfile
from pathlib import Path
import logging
import resource
import sys
import time

logger = logging.getLogger(__name__)

class LaTeXService:
    def __init__(self):
        pass
        
    
    def _set_resource_limits(self, cpu_time: int = 30):
        """
        Set resource limits for LaTeX compilation process
        
        Args:
            cpu_time: Maximum CPU time in seconds (default: 30)
        """
        try:
            # Limit CPU time
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_time, cpu_time))
            
            # Limit memory to 512MB
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
            
            # Limit output file size to 50MB
            resource.setrlimit(resource.RLIMIT_FSIZE, (50 * 1024 * 1024, 50 * 1024 * 1024))
            
            # Limit number of processes
            resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))
            
        except (ValueError, OSError) as e:
            logger.warning(f"Could not set resource limits: {e}")
    
    def compile_latex(self, tex_file: Path, output_dir: Path, timeout: int = 30) -> Path:
        """
        Compile LaTeX file to PDF with security restrictions
        
        Args:
            tex_file: Path to the .tex file to compile
            output_dir: Directory for output files
            timeout: Maximum compilation time in seconds (default: 30)
        
        Returns:
            Path to the generated PDF file
        
        Raises:
            LaTeXCompilationError: If compilation fails or times out
        """
        try:
            if not tex_file.exists():
                raise LaTeXCompilationError("Input file not found")
            
            # Set up resource limits for non-Windows platforms
            if sys.platform != 'win32':
                preexec_fn = lambda: self._set_resource_limits(cpu_time=timeout)
            else:
                preexec_fn = None
            
            result = subprocess.run([
                'pdflatex',
                '-no-shell-escape',  # CRITICAL: Disable shell command execution
                '-interaction=nonstopmode',
                '-output-directory', str(output_dir),
                str(tex_file)
            ], capture_output=True, text=True, timeout=timeout, preexec_fn=preexec_fn)
            
            if result.returncode != 0:
                error_msg = f"LaTeX compilation failed (return code {result.returncode}): {result.stderr or result.stdout}"
                logger.error(error_msg)
                raise LaTeXCompilationError(error_msg)
            
            # Check for PDF file
            pdf_file = output_dir / f"{tex_file.stem}.pdf"
            if not pdf_file.exists():
                raise LaTeXCompilationError("PDF file was not generated")
            
            return pdf_file
            
        except subprocess.TimeoutExpired:
            raise LaTeXCompilationError(
                f"LaTeX compilation timed out after {timeout} seconds. "
                "Your resume may be too complex. Try simplifying the content or reducing sections."
            )
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
