"""
Skills model
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Skill(Base):
    """User skills model"""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)

    # Relationships
    user = relationship("User", back_populates="skills")

    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}')>"


