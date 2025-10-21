"""Simplify skill model and remove tool classes

Revision ID: 0c823bff6ca1
Revises: 7804eac01555
Create Date: 2025-10-20 12:06:13.628291

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c823bff6ca1'
down_revision = '7804eac01555'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the experience_tools table first (due to foreign key constraints)
    op.drop_table('experience_tools')
    
    # Drop the tools table
    op.drop_table('tools')
    
    # Remove columns from skills table
    op.drop_column('skills', 'proficiency')
    op.drop_column('skills', 'years_experience')
    op.drop_column('skills', 'source')


def downgrade() -> None:
    # Add back columns to skills table
    op.add_column('skills', sa.Column('source', sa.String(50), nullable=True))
    op.add_column('skills', sa.Column('years_experience', sa.Numeric(3, 1), nullable=True))
    op.add_column('skills', sa.Column('proficiency', sa.String(50), nullable=True))
    
    # Recreate tools table
    op.create_table('tools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Recreate experience_tools table
    op.create_table('experience_tools',
        sa.Column('experience_id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['experience_id'], ['experiences.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('experience_id', 'tool_id')
    )
