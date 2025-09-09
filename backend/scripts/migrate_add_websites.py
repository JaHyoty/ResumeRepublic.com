#!/usr/bin/env python3
"""
Migration script to add websites table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Run the migration to add websites table"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Create websites table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS websites (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    site_name VARCHAR(255) NOT NULL,
                    url VARCHAR(500) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            # Create index on user_id for better query performance
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_websites_user_id ON websites(user_id)
            """))
            
            # Commit transaction
            trans.commit()
            print("✅ Websites table created successfully")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"❌ Error creating websites table: {e}")
            raise

if __name__ == "__main__":
    run_migration()
