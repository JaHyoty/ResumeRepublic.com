#!/usr/bin/env python3
"""
Migration script to add pdf_content column to resume_versions table
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate_add_pdf_content():
    """Add pdf_content column to resume_versions table"""
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Add pdf_content column
                print("Adding pdf_content column to resume_versions table...")
                conn.execute(text("""
                    ALTER TABLE resume_versions 
                    ADD COLUMN pdf_content TEXT;
                """))
                
                # Commit transaction
                trans.commit()
                print("✅ Successfully added pdf_content column to resume_versions table")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Error adding pdf_content column: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise

if __name__ == "__main__":
    migrate_add_pdf_content()
