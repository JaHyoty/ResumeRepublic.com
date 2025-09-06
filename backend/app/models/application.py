"""
Application model for job applications
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Application(Base):
    """Job application model"""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_title = Column(String(255), nullable=False)
    company = Column(String(100), nullable=False)
    job_description = Column(Text, nullable=True)
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

    # Relationships
    user = relationship("User", back_populates="applications")

    def __repr__(self):
        return f"<Application(id={self.id}, job_title='{self.job_title}', company='{self.company}')>"
