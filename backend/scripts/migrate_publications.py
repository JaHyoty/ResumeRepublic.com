"""
Migration script to add publisher field to publications table
"""

import asyncio
from sqlalchemy import create_engine, text
from app.core.database import engine
from app.core.config import settings


def migrate_publications_table():
    """Add publisher field to publications table"""
    print("Starting publications table migration...")
    
    with engine.connect() as conn:
        # Start a transaction
        trans = conn.begin()
        try:
            # Check if the publisher column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'publications' 
                AND column_name = 'publisher'
            """))
            existing_column = result.fetchone()
            
            if not existing_column:
                print("Adding publisher column...")
                conn.execute(text("ALTER TABLE publications ADD COLUMN publisher VARCHAR(255)"))
                print("Publisher column added successfully!")
            else:
                print("Publisher column already exists. No migration needed.")
                
            # Commit the transaction
            trans.commit()
            
        except Exception as e:
            print(f"Migration failed: {e}")
            trans.rollback()
            raise


if __name__ == "__main__":
    migrate_publications_table()
