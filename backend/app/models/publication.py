"""
Publications and certifications models
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


class Certification(Base):
    """Certifications model"""
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    issuing_organization = Column(String(150), nullable=True)
    date_obtained = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    credential_url = Column(String(500), nullable=True)
    credential_id = Column(String(100), nullable=True)  # Certificate ID or number

    # Relationships
    user = relationship("User", back_populates="certifications")

    def __repr__(self):
        return f"<Certification(id={self.id}, name='{self.name}')>"
