"""
Template utilities for resume generation
"""

import os
from pathlib import Path


def get_full_template_content(template_name: str = "ResumeTemplate1.tex") -> str:
    """
    Get the complete LaTeX template content including preamble
    """
    template_path = Path(__file__).parent.parent / "templates" / template_name
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content

def extract_template_content(template_name: str = "ResumeTemplate1.tex") -> str:
    """
    Extract the LaTeX content after \\begin{document} from the template file
    """
    template_path = Path(__file__).parent.parent / "templates" / template_name
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the \\begin{document} tag
    begin_doc_index = content.find('\\begin{document}')
    
    if begin_doc_index == -1:
        raise ValueError("Template file does not contain \\begin{document} tag")
    
    # Extract everything from \\begin{document} onwards
    template_content = content[begin_doc_index:]
    
    return template_content
