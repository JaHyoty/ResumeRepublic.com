"""Remove job data columns from applications table

Revision ID: refactor_applications
Revises: add_job_posting_parsing
Create Date: 2025-10-07 22:48:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'refactor_applications'
down_revision = 'add_job_posting_parsing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove job data columns from applications table
    # Job data is now fetched from job_postings table via job_posting_id
    op.drop_column('applications', 'job_title')
    op.drop_column('applications', 'company')
    op.drop_column('applications', 'job_description')


def downgrade() -> None:
    # Add back job data columns
    op.add_column('applications', sa.Column('job_title', sa.String(length=255), nullable=False))
    op.add_column('applications', sa.Column('company', sa.String(length=100), nullable=False))
    op.add_column('applications', sa.Column('job_description', sa.Text(), nullable=True))
    
    # Note: Data will be lost on downgrade since we can't easily restore it
    # This is expected as we're removing redundant data
