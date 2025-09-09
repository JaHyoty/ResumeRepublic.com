"""
Resume versioning models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ResumeVersion(Base):
    """Resume version model - linked to applications"""
    __tablename__ = "resume_versions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)  # e.g., "Software Engineer - Google"
    template_used = Column(String(100), nullable=True)  # e.g., "professional", "modern", "academic"
    latex_content = Column(Text, nullable=True)  # Generated LaTeX content
    pdf_url = Column(String(500), nullable=True)  # URL to stored PDF
    pdf_content = Column(Text, nullable=True)  # Base64-encoded PDF content
    resume_metadata = Column(JSON, nullable=True)  # Additional metadata (optimization settings, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="resume_versions")
    application = relationship("Application", back_populates="resume_versions")

    def __repr__(self):
        return f"<ResumeVersion(id={self.id}, title='{self.title}', application_id={self.application_id})>"
