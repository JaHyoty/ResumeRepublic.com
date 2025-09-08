"""
Migration script to update certifications table structure
"""

import asyncio
from sqlalchemy import create_engine, text
from app.core.database import engine
from app.core.config import settings


def migrate_certifications_table():
    """Migrate certifications table to new schema"""
    print("Starting certifications table migration...")
    
    with engine.connect() as conn:
        # Start a transaction
        trans = conn.begin()
        try:
            # Check if the old columns exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'certifications' 
                AND column_name IN ('issuing_organization', 'date_obtained', 'expiration_date')
            """))
            old_columns = [row[0] for row in result.fetchall()]
            
            if old_columns:
                print(f"Found old columns: {old_columns}")
                
                # Add new columns
                print("Adding new columns...")
                conn.execute(text("ALTER TABLE certifications ADD COLUMN IF NOT EXISTS issuer VARCHAR(255)"))
                conn.execute(text("ALTER TABLE certifications ADD COLUMN IF NOT EXISTS issue_date DATE"))
                conn.execute(text("ALTER TABLE certifications ADD COLUMN IF NOT EXISTS expiry_date DATE"))
                conn.execute(text("ALTER TABLE certifications ADD COLUMN IF NOT EXISTS credential_id VARCHAR(255)"))
                conn.execute(text("ALTER TABLE certifications ADD COLUMN IF NOT EXISTS credential_url TEXT"))
                
                # Migrate data from old columns to new columns
                print("Migrating data...")
                conn.execute(text("""
                    UPDATE certifications 
                    SET issuer = issuing_organization,
                        issue_date = date_obtained,
                        expiry_date = expiration_date
                    WHERE issuing_organization IS NOT NULL OR date_obtained IS NOT NULL OR expiration_date IS NOT NULL
                """))
                
                # Make new columns NOT NULL where we have data
                print("Updating column constraints...")
                conn.execute(text("ALTER TABLE certifications ALTER COLUMN issuer SET NOT NULL"))
                conn.execute(text("ALTER TABLE certifications ALTER COLUMN issue_date SET NOT NULL"))
                
                # Drop old columns
                print("Dropping old columns...")
                for column in old_columns:
                    conn.execute(text(f"ALTER TABLE certifications DROP COLUMN IF EXISTS {column}"))
                
                print("Migration completed successfully!")
            else:
                print("No old columns found. Table may already be up to date.")
                
            # Commit the transaction
            trans.commit()
            
        except Exception as e:
            print(f"Migration failed: {e}")
            trans.rollback()
            raise


if __name__ == "__main__":
    migrate_certifications_table()
