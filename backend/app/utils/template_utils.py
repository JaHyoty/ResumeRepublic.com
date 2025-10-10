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


def extract_document_content(latex_content: str) -> str:
    """
    Extract content between \\begin{document} and \\end{document} tags
    """
    begin_doc = latex_content.find('\\begin{document}')
    end_doc = latex_content.find('\\end{document}')
    
    if begin_doc == -1 or end_doc == -1:
        raise ValueError("LaTeX content must contain both \\begin{document} and \\end{document} tags")
    
    # Extract content between the tags (including the tags themselves)
    document_content = latex_content[begin_doc:end_doc + len('\\end{document}')]
    return document_content


def combine_with_template_preamble(document_content: str, template_name: str = "ResumeTemplate1.tex") -> str:
    """
    Combine document content with template preamble to create complete LaTeX
    """
    # Get the full template content
    full_template = get_full_template_content(template_name)
    
    # Find the end of the preamble (before \begin{document})
    preamble_end = full_template.find("\\begin{document}")
    if preamble_end == -1:
        # If no \begin{document} found, use the entire template
        return full_template
    
    # Extract preamble
    preamble = full_template[:preamble_end]
    
    # Find the end of the document
    document_end = full_template.find("\\end{document}")
    if document_end == -1:
        document_end = len(full_template)
    
    # Extract the closing
    closing = full_template[document_end:]
    
    # Combine: preamble + document content + closing
    complete_latex = preamble + document_content + closing
    
    return complete_latex
