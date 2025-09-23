"""remove_achievements_table

Revision ID: 22e67c0fb921
Revises: d3f03f34be49
Create Date: 2025-09-21 17:55:36.266559

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22e67c0fb921'
down_revision = 'd3f03f34be49'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the achievements table and its index
    op.drop_index(op.f('ix_achievements_id'), table_name='achievements')
    op.drop_table('achievements')


def downgrade() -> None:
    # Recreate the achievements table
    op.create_table('achievements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('experience_id', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['experience_id'], ['experiences.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_achievements_id'), 'achievements', ['id'], unique=False)
