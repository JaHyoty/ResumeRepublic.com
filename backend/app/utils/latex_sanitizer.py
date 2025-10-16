"""
LaTeX Security Sanitizer

This module provides security validation for user-provided LaTeX content
to prevent code execution, file system access, and DoS attacks.
"""

import re
import logging
from typing import Set

logger = logging.getLogger(__name__)


class LaTeXSecurityError(Exception):
    """Raised when dangerous LaTeX content is detected"""
    pass


# Dangerous LaTeX commands that could lead to security vulnerabilities
DANGEROUS_COMMANDS = [
    r'\\write18',           # Shell escape command
    r'\\immediate\\write',  # Immediate write (can be used for shell escape)
    r'\\input\s*\{?\s*[|/]',  # Absolute paths or pipe input
    r'\\include\s*\{?\s*[|/]',  # Absolute paths or pipe include
    r'\\openin',            # Open file for reading
    r'\\openout',           # Open file for writing
    r'\\read',              # Read from file
    r'\\write\s+',          # Write to file (when not write18)
    r'\\special',           # Special commands (driver-specific)
    r'\\pdfliteral',        # PDF literal commands
    r'\\pdfobj',            # PDF object creation
    r'\\directlua',         # LuaTeX Lua execution
    r'\\ShellEscape',       # Alternative shell escape
    r'\\csname\s*.*?endcsname',  # Command sequence name (can bypass filters)
    r'\\catcode',           # Change character category (can break parser)
    r'\\let',               # Command aliasing (can bypass filters)
    r'\\def\\write',        # Redefining write command
    r'\\def\\input',        # Redefining input command
    r'\\expandafter.*?\\write',  # Expanded write commands
    r'\\meaning',           # Can expose internals
    r'\\show',              # Can expose command definitions
]

# Potentially dangerous packages that could be abused
DANGEROUS_PACKAGES = [
    'verbatim',    # Can include raw content bypassing filters
    'listings',    # Can include raw code
    'minted',      # Requires shell escape for syntax highlighting
    'pythontex',   # Executes Python code
    'sagetex',     # Executes SageMath code
    'pst-pdf',     # PostScript execution
    'auto-pst-pdf', # PostScript execution
    'bashful',     # Shell script execution
    'lua',         # Lua execution
]

# Whitelist of allowed packages for resume generation
ALLOWED_PACKAGES: Set[str] = {
    # Fonts and text formatting
    'fontspec', 'fontenc', 'inputenc', 'lmodern', 'fontawesome', 'fontawesome5',
    'textcomp', 'microtype', 'csquotes',
    
    # Page layout and geometry
    'geometry', 'fancyhdr', 'lastpage', 'multicol', 'parskip', 'setspace',
    'titlesec', 'titling',
    
    # Colors and graphics
    'xcolor', 'color', 'graphicx', 'tikz', 'pgf',
    
    # Lists and enumerations
    'enumitem', 'etoolbox',
    
    # Tables
    'tabularx', 'array', 'multirow', 'booktabs', 'longtable', 'colortbl',
    
    # Hyperlinks and PDF features
    'hyperref', 'url', 'nameref',
    
    # Math (if needed for resumes)
    'amsmath', 'amssymb', 'amsfonts',
    
    # Other common resume packages
    'ragged2e', 'soul', 'ulem', 'babel', 'polyglossia',
    'calc', 'ifthen', 'xifthen', 'datetime', 'advdate',
}


def sanitize_latex(latex_content: str, max_size: int = 1_000_000) -> str:
    """
    Sanitize user-provided LaTeX content for security
    
    Args:
        latex_content: The LaTeX content to sanitize
        max_size: Maximum allowed content size in bytes (default 1MB)
    
    Returns:
        The sanitized LaTeX content (unchanged if valid)
    
    Raises:
        LaTeXSecurityError: If dangerous content is detected
    """
    if not latex_content:
        raise LaTeXSecurityError("LaTeX content cannot be empty")
    
    # Check document size
    if len(latex_content) > max_size:
        raise LaTeXSecurityError(
            f"LaTeX content exceeds maximum size of {max_size} bytes"
        )
    
    # Log security check
    logger.debug(f"Sanitizing LaTeX content ({len(latex_content)} bytes)")
    
    # Check for dangerous commands
    for pattern in DANGEROUS_COMMANDS:
        matches = re.search(pattern, latex_content, re.IGNORECASE | re.MULTILINE)
        if matches:
            logger.warning(
                f"Blocked LaTeX security violation: pattern '{pattern}' matched",
                extra={'matched_text': matches.group(0)[:100]}
            )
            raise LaTeXSecurityError(
                f"Forbidden LaTeX command detected. Security violation: {pattern}"
            )
    
    # Check for absolute paths in file inclusion commands
    absolute_path_pattern = r'\\(input|include|includegraphics)\s*\{?\s*[/~]'
    if re.search(absolute_path_pattern, latex_content, re.IGNORECASE):
        raise LaTeXSecurityError(
            "Absolute file paths are not allowed in \\input, \\include, or \\includegraphics"
        )
    
    # Check for path traversal attempts
    if '..' in latex_content:
        # Allow .. in normal text but not in commands
        path_traversal_pattern = r'\\(input|include|includegraphics)\s*\{[^}]*\.\.[^}]*\}'
        if re.search(path_traversal_pattern, latex_content):
            raise LaTeXSecurityError(
                "Path traversal attempts are not allowed"
            )
    
    # Check for pipe characters (command execution)
    # Allow pipes in normal text but not in commands
    if '|' in latex_content:
        pipe_in_command = r'\\(input|include|includegraphics)\s*\{[^}]*\|'
        if re.search(pipe_in_command, latex_content):
            raise LaTeXSecurityError(
                "Pipe characters in file inclusion commands are not allowed"
            )
    
    # Validate package imports
    _validate_packages(latex_content)
    
    # Check for excessive nesting (DoS prevention)
    _check_nesting_depth(latex_content)
    
    # Check for potential infinite loops
    _check_for_loops(latex_content)
    
    # Check for excessive repetition (DoS prevention)
    _check_repetition(latex_content)
    
    logger.debug("LaTeX content passed all security checks")
    return latex_content


def _validate_packages(latex_content: str) -> None:
    """Validate that only allowed packages are used"""
    # Match \usepackage with optional parameters
    package_pattern = r'\\usepackage\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}'
    
    for match in re.finditer(package_pattern, latex_content, re.IGNORECASE):
        packages_str = match.group(1)
        # Handle multiple packages in one \usepackage command
        packages = [pkg.strip() for pkg in packages_str.split(',')]
        
        for pkg in packages:
            # Check against dangerous packages
            if pkg.lower() in DANGEROUS_PACKAGES:
                logger.warning(f"Blocked dangerous package: {pkg}")
                raise LaTeXSecurityError(
                    f"Package '{pkg}' is not allowed due to security concerns"
                )
            
            # Check against whitelist
            if pkg.lower() not in ALLOWED_PACKAGES:
                logger.info(f"Blocked non-whitelisted package: {pkg}")
                raise LaTeXSecurityError(
                    f"Package '{pkg}' is not in the allowed list. "
                    f"Contact support to request package approval."
                )


def _check_nesting_depth(latex_content: str, max_depth: int = 50) -> None:
    """Check for excessive brace nesting (DoS prevention)"""
    brace_depth = 0
    max_observed_depth = 0
    
    for char in latex_content:
        if char == '{':
            brace_depth += 1
            max_observed_depth = max(max_observed_depth, brace_depth)
        elif char == '}':
            brace_depth -= 1
    
    if max_observed_depth > max_depth:
        raise LaTeXSecurityError(
            f"Excessive nesting detected ({max_observed_depth} levels). "
            f"Maximum allowed: {max_depth}"
        )
    
    # Check for unbalanced braces
    if brace_depth != 0:
        raise LaTeXSecurityError(
            f"Unbalanced braces detected (net depth: {brace_depth})"
        )


def _check_for_loops(latex_content: str) -> None:
    """Check for potentially infinite loops"""
    # Check for recursive macro definitions (e.g., \def\x{\x}\x)
    # Pattern: \def\MACRO{...\MACRO...}
    recursive_def_pattern = r'\\def\\([a-zA-Z]+)\{[^}]*\\(?:1|[a-zA-Z]+)[^}]*\}'
    # More specific: look for \def\x{...\x...} pattern
    simple_recursive = r'\\def\\([a-zA-Z])\{[^}]*\\\1[^}]*\}'
    if re.search(simple_recursive, latex_content):
        raise LaTeXSecurityError(
            "Recursive macro definitions are not allowed (potential infinite loop)"
        )
    
    # Check for excessive loop constructs
    loop_pattern = r'\\(loop|repeat|foreach|for)'
    loop_matches = re.findall(loop_pattern, latex_content, re.IGNORECASE)
    if len(loop_matches) > 10:
        raise LaTeXSecurityError(
            f"Too many loop constructs detected ({len(loop_matches)}). Maximum: 10"
        )


def _check_repetition(latex_content: str) -> None:
    """Check for excessive repetition that could cause DoS"""
    # Check for very large numeric ranges
    large_range_pattern = r'\\foreach\s+\\[a-zA-Z]+\s+in\s+\{1\s*,\s*\.\.\.\s*,\s*(\d+)\}'
    for match in re.finditer(large_range_pattern, latex_content):
        max_value = int(match.group(1))
        if max_value > 1000:
            raise LaTeXSecurityError(
                f"Loop range too large ({max_value}). Maximum: 1000"
            )
    
    # Check for repeated sections/subsections
    section_pattern = r'\\(section|subsection|subsubsection)\{'
    section_count = len(re.findall(section_pattern, latex_content))
    if section_count > 100:
        raise LaTeXSecurityError(
            f"Too many sections ({section_count}). Maximum: 100"
        )


def validate_user_latex(latex_content: str) -> None:
    """
    Complete validation for user-provided LaTeX content
    
    This function performs both structural and security validation.
    
    Args:
        latex_content: The LaTeX content to validate
    
    Raises:
        ValueError: For structural validation errors
        LaTeXSecurityError: For security violations
    """
    # Basic structural validation
    if not latex_content or not latex_content.strip():
        raise ValueError("LaTeX content cannot be empty")
    
    if '\\begin{document}' not in latex_content:
        raise ValueError("LaTeX content must contain \\begin{document}")
    
    if '\\end{document}' not in latex_content:
        raise ValueError("LaTeX content must contain \\end{document}")
    
    # Security validation
    sanitize_latex(latex_content)
    
    logger.info("LaTeX content validated successfully")


# Export main functions
__all__ = ['sanitize_latex', 'validate_user_latex', 'LaTeXSecurityError']

