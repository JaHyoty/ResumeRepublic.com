"""drop domain_selectors table

Revision ID: drop_domain_selectors_table
Revises: refactor_applications
Create Date: 2025-10-08 16:27:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'drop_domain_selectors_table'
down_revision = 'refactor_applications'
branch_labels = None
depends_on = None


def upgrade():
    """Drop domain_selectors table"""
    # Drop the domain_selectors table
    op.drop_index('ix_domain_selectors_domain', table_name='domain_selectors')
    op.drop_table('domain_selectors')


def downgrade():
    """Recreate domain_selectors table"""
    # Recreate the domain_selectors table
    op.create_table('domain_selectors',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('selectors', sa.JSON(), nullable=False),
        sa.Column('last_success', sa.DateTime(timezone=True), nullable=True),
        sa.Column('success_count', sa.Integer(), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_domain_selectors_domain', 'domain_selectors', ['domain'], unique=True)
