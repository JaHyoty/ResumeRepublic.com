"""simplify_project_model

Revision ID: 2025_09_30_1544
Revises: 2025_09_25_1300
Create Date: 2025-09-30 15:44:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'simplify_project_model'
down_revision = 'remove_deprecated_resume_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add technologies_used column to projects table
    op.add_column('projects', sa.Column('technologies_used', sa.Text(), nullable=True))
    
    # Migrate data from project_technologies to technologies_used
    # First, get all projects with their technologies
    connection = op.get_bind()
    
    # Get all projects and their technologies
    projects_with_techs = connection.execute(sa.text("""
        SELECT p.id, string_agg(pt.technology, ', ' ORDER BY pt.id) as technologies
        FROM projects p
        LEFT JOIN project_technologies pt ON p.id = pt.project_id
        GROUP BY p.id
    """)).fetchall()
    
    # Update projects with concatenated technologies
    for project_id, technologies in projects_with_techs:
        if technologies:
            connection.execute(sa.text("""
                UPDATE projects 
                SET technologies_used = :technologies 
                WHERE id = :project_id
            """), {"technologies": technologies, "project_id": project_id})
    
    # Drop the related tables
    op.drop_table('project_achievements')
    op.drop_table('project_technologies')


def downgrade() -> None:
    # Recreate the tables
    op.create_table('project_technologies',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('technology', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='project_technologies_project_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='project_technologies_pkey')
    )
    op.create_index('ix_project_technologies_id', 'project_technologies', ['id'], unique=False)
    
    op.create_table('project_achievements',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('description', sa.TEXT(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='project_achievements_project_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='project_achievements_pkey')
    )
    op.create_index('ix_project_achievements_id', 'project_achievements', ['id'], unique=False)
    
    # Migrate data back from technologies_used to project_technologies
    connection = op.get_bind()
    
    # Get all projects with technologies_used
    projects_with_techs = connection.execute(sa.text("""
        SELECT id, technologies_used 
        FROM projects 
        WHERE technologies_used IS NOT NULL AND technologies_used != ''
    """)).fetchall()
    
    # Split technologies and insert into project_technologies table
    for project_id, technologies_used in projects_with_techs:
        if technologies_used:
            technologies = [tech.strip() for tech in technologies_used.split(',') if tech.strip()]
            for tech in technologies:
                connection.execute(sa.text("""
                    INSERT INTO project_technologies (project_id, technology) 
                    VALUES (:project_id, :technology)
                """), {"project_id": project_id, "technology": tech})
    
    # Drop the technologies_used column
    op.drop_column('projects', 'technologies_used')
