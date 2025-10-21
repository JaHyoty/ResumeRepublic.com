"""
Project model for personal and professional projects
"""

from sqlalchemy import Column, Integer, String, Date, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Project(Base):
    """Project model"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    role = Column(String(255), nullable=True)  # New field for role
    start_date = Column(Date, nullable=True)  # Made optional
    end_date = Column(Date, nullable=True)  # None for ongoing projects
    url = Column(String(500), nullable=True)
    is_current = Column(Boolean, default=False)
    technologies_used = Column(Text, nullable=True)  # Comma-separated text field

    # Relationships
    user = relationship("User", back_populates="projects")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"