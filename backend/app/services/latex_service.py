"""
LaTeX resume generation service
"""
import subprocess
import tempfile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class LaTeXService:
    def __init__(self):
        pass
        
    
    def compile_latex(self, tex_file: Path, output_dir: Path) -> Path:
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
