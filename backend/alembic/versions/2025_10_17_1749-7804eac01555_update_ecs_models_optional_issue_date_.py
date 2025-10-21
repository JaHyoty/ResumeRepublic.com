"""Update ECS models: optional issue_date, mandatory end_date/field_of_study, rename co_authors, add role field, optional start_date

Revision ID: 7804eac01555
Revises: drop_domain_selectors_table
Create Date: 2025-10-17 17:49:59.478027

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7804eac01555'
down_revision = 'drop_domain_selectors_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make issue_date optional in certifications
    op.alter_column('certifications', 'issue_date',
                    existing_type=sa.DATE(),
                    nullable=True)
    
    # Make end_date mandatory and field_of_study mandatory in education
    op.alter_column('education', 'end_date',
                    existing_type=sa.DATE(),
                    nullable=False)
    op.alter_column('education', 'field_of_study',
                    existing_type=sa.VARCHAR(length=255),
                    nullable=False)
    
    # Rename description to coursework in education
    op.alter_column('education', 'description',
                    new_column_name='coursework',
                    existing_type=sa.TEXT(),
                    nullable=True)
    
    # Remove location and website_url from education
    op.drop_column('education', 'location')
    op.drop_column('education', 'website_url')
    
    # Rename co_authors to authors in publications
    op.alter_column('publications', 'co_authors',
                    new_column_name='authors',
                    existing_type=sa.TEXT(),
                    nullable=True)
    
    # Add role field to projects and make start_date optional
    op.add_column('projects', sa.Column('role', sa.String(length=255), nullable=True))
    op.alter_column('projects', 'start_date',
                    existing_type=sa.DATE(),
                    nullable=True)


def downgrade() -> None:
    # Revert projects changes
    op.alter_column('projects', 'start_date',
                    existing_type=sa.DATE(),
                    nullable=False)
    op.drop_column('projects', 'role')
    
    # Revert publications changes
    op.alter_column('publications', 'authors',
                    new_column_name='co_authors',
                    existing_type=sa.TEXT(),
                    nullable=True)
    
    # Revert education changes
    op.add_column('education', sa.Column('website_url', sa.VARCHAR(length=500), nullable=True))
    op.add_column('education', sa.Column('location', sa.VARCHAR(length=255), nullable=True))
    op.alter_column('education', 'coursework',
                    new_column_name='description',
                    existing_type=sa.TEXT(),
                    nullable=True)
    op.alter_column('education', 'field_of_study',
                    existing_type=sa.VARCHAR(length=255),
                    nullable=True)
    op.alter_column('education', 'end_date',
                    existing_type=sa.DATE(),
                    nullable=True)
    
    # Revert certifications changes
    op.alter_column('certifications', 'issue_date',
                    existing_type=sa.DATE(),
                    nullable=False)
