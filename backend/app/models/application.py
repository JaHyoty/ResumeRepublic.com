"""
Application model for job applications
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Application(Base):
    """Job application model"""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    applied_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Application status flags
    online_assessment = Column(Boolean, default=False)
    interview = Column(Boolean, default=False)
    rejected = Column(Boolean, default=False)
    
    # Additional metadata
    salary_range = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)
    job_type = Column(String(50), nullable=True)  # Full-time, Part-time, Contract, etc.
    experience_level = Column(String(50), nullable=True)  # Entry, Mid, Senior, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional metadata as JSON
    application_metadata = Column(JSON, nullable=True)
    
    # Job posting reference (optional)
    job_posting_id = Column(UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="applications")
    resume_versions = relationship("ResumeVersion", back_populates="application", cascade="all, delete-orphan")
    job_posting = relationship("JobPosting", foreign_keys=[job_posting_id])

    def __repr__(self):
        return f"<Application(id={self.id}, job_title='{self.job_title}', company='{self.company}')>"
