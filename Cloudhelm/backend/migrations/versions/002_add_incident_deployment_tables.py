"""Add incident and deployment tables

Revision ID: 002
Revises: 001
Create Date: 2024-02-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create incidents table
    op.create_table(
        'incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('created_at', sa.Date(), nullable=False),
        sa.Column('resolved_at', sa.Date(), nullable=True),
        sa.Column('service', sa.String(100), nullable=True),
        sa.Column('team', sa.String(100), nullable=True),
        sa.Column('env', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_incidents_id'), 'incidents', ['id'], unique=False)
    op.create_index(op.f('ix_incidents_status'), 'incidents', ['status'], unique=False)
    op.create_index(op.f('ix_incidents_severity'), 'incidents', ['severity'], unique=False)
    op.create_index(op.f('ix_incidents_created_at'), 'incidents', ['created_at'], unique=False)
    op.create_index('idx_incident_status_created', 'incidents', ['status', 'created_at'], unique=False)
    
    # Create deployments table
    op.create_table(
        'deployments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service', sa.String(100), nullable=False),
        sa.Column('environment', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('deployed_at', sa.Date(), nullable=False),
        sa.Column('deployed_by', sa.String(100), nullable=True),
        sa.Column('version', sa.String(100), nullable=True),
        sa.Column('commit_sha', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deployments_id'), 'deployments', ['id'], unique=False)
    op.create_index(op.f('ix_deployments_service'), 'deployments', ['service'], unique=False)
    op.create_index(op.f('ix_deployments_status'), 'deployments', ['status'], unique=False)
    op.create_index(op.f('ix_deployments_deployed_at'), 'deployments', ['deployed_at'], unique=False)
    op.create_index('idx_deployment_deployed_at_status', 'deployments', ['deployed_at', 'status'], unique=False)
    op.create_index('idx_deployment_service_env', 'deployments', ['service', 'environment'], unique=False)


def downgrade() -> None:
    op.drop_table('deployments')
    op.drop_table('incidents')
