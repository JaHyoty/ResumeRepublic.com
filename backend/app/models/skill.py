"""
Skills and tools models
"""

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.database import Base


class Skill(Base):
    """User skills model"""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    proficiency = Column(String(50), nullable=True)  # e.g., "Beginner", "Intermediate", "Advanced", "Expert"
    years_experience = Column(Numeric(3, 1), nullable=True)  # e.g., 2.5 years
    source = Column(String(50), nullable=True)  # e.g., "work", "education", "certification"

    # Relationships
    user = relationship("User", back_populates="skills")

    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}', proficiency='{self.proficiency}')>"


class Tool(Base):
    """Tools and technologies model"""
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=True)  # e.g., "Programming Language", "Framework", "Database"

    # Relationships
    experiences = relationship("ExperienceTool", back_populates="tool")

    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}')>"


# Association table for experience-tool many-to-many relationship
class ExperienceTool(Base):
    """Association table for experience-tool relationship"""
    __tablename__ = "experience_tools"

    experience_id = Column(Integer, ForeignKey("experiences.id", ondelete="CASCADE"), primary_key=True)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    experience = relationship("Experience", back_populates="tools")
    tool = relationship("Tool", back_populates="experiences")

    def __repr__(self):
        return f"<ExperienceTool(experience_id={self.experience_id}, tool_id={self.tool_id})>"
