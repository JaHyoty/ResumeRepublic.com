#!/usr/bin/env python3
"""
Migration script to refactor resume schema to link with applications
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate_resume_schema():
    """Refactor resume schema to link with applications"""
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                print("Refactoring resume schema to link with applications...")
                
                # Drop job_descriptions table if it exists
                print("Dropping job_descriptions table...")
                conn.execute(text("DROP TABLE IF EXISTS job_descriptions CASCADE"))
                
                # Add application_id column to resume_versions
                print("Adding application_id column to resume_versions...")
                conn.execute(text("""
                    ALTER TABLE resume_versions 
                    ADD COLUMN IF NOT EXISTS application_id INTEGER
                """))
                
                # Add template_used column to resume_versions
                print("Adding template_used column to resume_versions...")
                conn.execute(text("""
                    ALTER TABLE resume_versions 
                    ADD COLUMN IF NOT EXISTS template_used VARCHAR(100)
                """))
                
                # Add foreign key constraint for application_id
                print("Adding foreign key constraint for application_id...")
                conn.execute(text("""
                    ALTER TABLE resume_versions 
                    ADD CONSTRAINT fk_resume_versions_application_id 
                    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
                """))
                
                # Drop the old job_description_id column and constraint
                print("Dropping old job_description_id column...")
                conn.execute(text("""
                    ALTER TABLE resume_versions 
                    DROP COLUMN IF EXISTS job_description_id
                """))
                
                # Make application_id NOT NULL after adding the constraint
                print("Making application_id NOT NULL...")
                conn.execute(text("""
                    ALTER TABLE resume_versions 
                    ALTER COLUMN application_id SET NOT NULL
                """))
                
                # Commit transaction
                trans.commit()
                print("✅ Successfully refactored resume schema")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Error refactoring resume schema: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise

if __name__ == "__main__":
    migrate_resume_schema()
