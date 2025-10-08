"""
Job posting parsing models
Handles parsing of job postings from URLs with multiple extraction methods
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, JSON, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class JobPosting(Base):
    """Job posting parsing model"""
    __tablename__ = "job_postings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    url = Column(String(2048), unique=True, nullable=True, index=True)
    domain = Column(String(255), nullable=True, index=True)
    
    # User who created this job posting
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Extracted job data
    title = Column(String(500), nullable=True)
    company = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Parsing status and metadata
    status = Column(
        String(20), 
        nullable=False, 
        default='pending',
        index=True
    )
    provenance = Column(JSON, nullable=True)  # Extraction method and confidence
    raw_snapshot = Column(JSON, nullable=True)  # Sanitized HTML snapshot
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    fetch_attempts = relationship("JobPostingFetchAttempt", back_populates="job_posting", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'fetching', 'failed', 'manual', 'complete')",
            name='check_job_posting_status'
        ),
    )

    def __repr__(self):
        return f"<JobPosting(id={self.id}, url='{self.url}', status='{self.status}')>"


class JobPostingFetchAttempt(Base):
    """Audit log for job posting fetch attempts"""
    __tablename__ = "job_posting_fetch_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    job_posting_id = Column(UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False)
    
    # Attempt details
    method = Column(String(50), nullable=False)  # 'schema', 'heuristic', 'llm', 'manual'
    response_code = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job_posting = relationship("JobPosting", back_populates="fetch_attempts")

    def __repr__(self):
        return f"<JobPostingFetchAttempt(id={self.id}, method='{self.method}', success={self.success})>"
