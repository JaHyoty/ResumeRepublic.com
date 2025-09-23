"""
Experience and related models
"""

from sqlalchemy import Column, Integer, String, Date, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Experience(Base):
    """Work experience model"""
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company = Column(String(100), nullable=False)
    location = Column(String(100), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # None for current position
    description = Column(Text, nullable=True)
    is_current = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="experiences")
    titles = relationship("ExperienceTitle", back_populates="experience", cascade="all, delete-orphan")
    tools = relationship("ExperienceTool", back_populates="experience", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Experience(id={self.id}, company='{self.company}')>"


class ExperienceTitle(Base):
    """Job titles for experiences"""
    __tablename__ = "experience_titles"

    id = Column(Integer, primary_key=True, index=True)
    experience_id = Column(Integer, ForeignKey("experiences.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(100), nullable=False)
    is_primary = Column(Boolean, default=False)

    # Relationships
    experience = relationship("Experience", back_populates="titles")

    def __repr__(self):
        return f"<ExperienceTitle(id={self.id}, title='{self.title}')>"


