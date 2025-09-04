"""
Resume versioning and job description models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ResumeVersion(Base):
    """Resume version model"""
    __tablename__ = "resume_versions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)  # e.g., "Software Engineer - Google"
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=True)
    latex_content = Column(Text, nullable=True)  # Generated LaTeX content
    pdf_url = Column(String(500), nullable=True)  # URL to stored PDF
    resume_metadata = Column(JSON, nullable=True)  # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="resume_versions")
    job_description = relationship("JobDescription", back_populates="resume_versions")

    def __repr__(self):
        return f"<ResumeVersion(id={self.id}, title='{self.title}')>"


class JobDescription(Base):
    """Job description model"""
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    company = Column(String(100), nullable=True)
    content = Column(Text, nullable=False)  # Full job description text
    extracted_keywords = Column(JSON, nullable=True)  # Extracted keywords and requirements
    salary_range = Column(String(100), nullable=True)  # e.g., "$80,000 - $120,000"
    location = Column(String(100), nullable=True)
    job_type = Column(String(50), nullable=True)  # e.g., "Full-time", "Part-time", "Contract"
    experience_level = Column(String(50), nullable=True)  # e.g., "Entry", "Mid", "Senior"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
    resume_versions = relationship("ResumeVersion", back_populates="job_description")

    def __repr__(self):
        return f"<JobDescription(id={self.id}, title='{self.title}', company='{self.company}')>"
