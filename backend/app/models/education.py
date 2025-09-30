"""
Education models
"""

from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Education(Base):
    """Education model"""
    __tablename__ = "education"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    institution = Column(String(255), nullable=False)
    degree = Column(String(255), nullable=False)
    field_of_study = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # None for current education
    gpa = Column(String(10), nullable=True)  # e.g., "3.85", "First Class", flexible format
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    website_url = Column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="education")

    def __repr__(self):
        return f"<Education(id={self.id}, institution='{self.institution}', degree='{self.degree}')>"
