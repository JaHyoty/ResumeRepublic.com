"""remove deprecated resume fields

Revision ID: 2025_09_25_1300
Revises: 2025_09_25_1245
Create Date: 2025-09-25 13:00:00.123456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_09_25_1300'
down_revision = '2025_09_25_1245'
branch_labels = None
depends_on = None


def upgrade():
    # Remove deprecated columns
    op.drop_column('resume_versions', 'pdf_content')
    op.drop_column('resume_versions', 'latex_content')


def downgrade():
    # Add back the deprecated columns
    op.add_column('resume_versions', sa.Column('pdf_content', sa.Text(), nullable=True))
    op.add_column('resume_versions', sa.Column('latex_content', sa.Text(), nullable=True))
