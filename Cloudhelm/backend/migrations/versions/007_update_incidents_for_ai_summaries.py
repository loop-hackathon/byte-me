"""update incidents for ai summaries

Revision ID: 007
Revises: 006
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to incidents table
    op.add_column('incidents', sa.Column('incident_id', sa.String(length=100), nullable=True))
    op.add_column('incidents', sa.Column('description', sa.String(), nullable=True))
    op.add_column('incidents', sa.Column('anomalies', sa.String(), nullable=True))
    op.add_column('incidents', sa.Column('recent_releases', sa.String(), nullable=True))
    op.add_column('incidents', sa.Column('metrics_summary', sa.String(), nullable=True))
    op.add_column('incidents', sa.Column('cost_changes', sa.String(), nullable=True))
    op.add_column('incidents', sa.Column('ai_summary', sa.String(), nullable=True))
    op.add_column('incidents', sa.Column('summary_generated_at', sa.Date(), nullable=True))
    
    # Create unique index on incident_id
    op.create_index('ix_incidents_incident_id', 'incidents', ['incident_id'], unique=True)
    
    # Create index on service and env
    op.create_index('ix_incidents_service_env', 'incidents', ['service', 'env'])
    
    # Update existing incidents to have incident_id (INC-{id})
    op.execute("""
        UPDATE incidents 
        SET incident_id = 'INC-' || LPAD(id::text, 6, '0')
        WHERE incident_id IS NULL
    """)
    
    # Make incident_id not nullable after populating
    op.alter_column('incidents', 'incident_id', nullable=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_incidents_service_env', table_name='incidents')
    op.drop_index('ix_incidents_incident_id', table_name='incidents')
    
    # Drop columns
    op.drop_column('incidents', 'summary_generated_at')
    op.drop_column('incidents', 'ai_summary')
    op.drop_column('incidents', 'cost_changes')
    op.drop_column('incidents', 'metrics_summary')
    op.drop_column('incidents', 'recent_releases')
    op.drop_column('incidents', 'anomalies')
    op.drop_column('incidents', 'description')
    op.drop_column('incidents', 'incident_id')
