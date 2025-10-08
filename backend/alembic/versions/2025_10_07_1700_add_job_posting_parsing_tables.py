"""Add job posting parsing tables

Revision ID: add_job_posting_parsing
Revises: simplify_project_model
Create Date: 2024-10-07 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_job_posting_parsing'
down_revision = 'simplify_project_model'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create job_postings table
    op.create_table('job_postings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('provenance', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('raw_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('pending', 'fetching', 'failed', 'manual', 'complete')", name='check_job_posting_status')
    )
    # Primary key automatically creates unique index, no need for explicit index
    op.create_index(op.f('ix_job_postings_url'), 'job_postings', ['url'], unique=True)
    op.create_index(op.f('ix_job_postings_domain'), 'job_postings', ['domain'], unique=False)
    op.create_index(op.f('ix_job_postings_status'), 'job_postings', ['status'], unique=False)

    # Create domain_selectors table
    op.create_table('domain_selectors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('selectors', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('last_success', sa.DateTime(timezone=True), nullable=True),
        sa.Column('success_count', sa.Integer(), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain')
    )
    # Primary key automatically creates unique index, no need for explicit index
    op.create_index(op.f('ix_domain_selectors_domain'), 'domain_selectors', ['domain'], unique=True)

    # Create job_posting_fetch_attempts table
    op.create_table('job_posting_fetch_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_posting_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('method', sa.String(length=50), nullable=False),
        sa.Column('response_code', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['job_posting_id'], ['job_postings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # Primary key automatically creates unique index, no need for explicit index


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('job_posting_fetch_attempts')
    
    op.drop_index(op.f('ix_domain_selectors_domain'), table_name='domain_selectors')
    op.drop_table('domain_selectors')
    
    op.drop_index(op.f('ix_job_postings_status'), table_name='job_postings')
    op.drop_index(op.f('ix_job_postings_domain'), table_name='job_postings')
    op.drop_index(op.f('ix_job_postings_url'), table_name='job_postings')
    op.drop_table('job_postings')
