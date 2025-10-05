"""add_terms_agreement_fields_to_user

Revision ID: add_terms_agreement_fields_to_user
Revises: simplify_project_model
Create Date: 2025-10-04 20:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_terms_agreement_to_user'
down_revision = 'simplify_project_model'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add terms and privacy policy agreement fields to users table
    op.add_column('users', sa.Column('terms_accepted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('privacy_policy_accepted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove terms and privacy policy agreement fields from users table
    op.drop_column('users', 'privacy_policy_accepted_at')
    op.drop_column('users', 'terms_accepted_at')
