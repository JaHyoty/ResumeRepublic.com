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
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # None for ongoing projects
    url = Column(String(500), nullable=True)
    is_current = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="projects")
    technologies = relationship("ProjectTechnology", back_populates="project", cascade="all, delete-orphan")
    achievements = relationship("ProjectAchievement", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class ProjectTechnology(Base):
    """Technologies used in projects"""
    __tablename__ = "project_technologies"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    technology = Column(String(100), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="technologies")

    def __repr__(self):
        return f"<ProjectTechnology(id={self.id}, technology='{self.technology}')>"


class ProjectAchievement(Base):
    """Achievements linked to projects"""
    __tablename__ = "project_achievements"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="achievements")

    def __repr__(self):
        return f"<ProjectAchievement(id={self.id}, description='{self.description[:50]}...')>"
