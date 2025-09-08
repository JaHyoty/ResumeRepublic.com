"""
Publications model
"""

from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Publication(Base):
    """Publications model"""
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    co_authors = Column(Text, nullable=True)
    publication_date = Column(Date, nullable=True)
    url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    publication_type = Column(String(50), nullable=True)  # e.g., "Journal", "Conference", "Blog", "Book"

    # Relationships
    user = relationship("User", back_populates="publications")

    def __repr__(self):
        return f"<Publication(id={self.id}, title='{self.title[:50]}...')>"
