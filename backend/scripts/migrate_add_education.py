#!/usr/bin/env python3
"""
Migration script to add education table
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate_add_education():
    """Add education table"""
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Create education table
                print("Creating education table...")
                conn.execute(text("""
                    CREATE TABLE education (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        institution VARCHAR(255) NOT NULL,
                        degree VARCHAR(255) NOT NULL,
                        field_of_study VARCHAR(255),
                        start_date DATE NOT NULL,
                        end_date DATE,
                        gpa VARCHAR(10),
                        description TEXT,
                        location VARCHAR(255),
                        website_url VARCHAR(500)
                    );
                """))
                
                # Create index on user_id for better query performance
                print("Creating index on user_id...")
                conn.execute(text("""
                    CREATE INDEX ix_education_user_id ON education(user_id);
                """))
                
                # Commit transaction
                trans.commit()
                print("✅ Successfully created education table")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Error creating education table: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise

if __name__ == "__main__":
    migrate_add_education()
