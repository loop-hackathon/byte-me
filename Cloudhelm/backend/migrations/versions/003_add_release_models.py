"""add release models

Revision ID: 003
Revises: 002
Create Date: 2024-02-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create repositories table
    op.create_table(
        'repositories',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('stars', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('owner', sa.String(), nullable=False),
        sa.Column('github_id', sa.Integer(), nullable=True),
        sa.Column('last_deployment', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_syncing', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('last_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_repository_owner_name', 'repositories', ['owner', 'name'])
    op.create_index(op.f('ix_repositories_full_name'), 'repositories', ['full_name'], unique=True)
    op.create_index(op.f('ix_repositories_github_id'), 'repositories', ['github_id'], unique=True)
    op.create_index(op.f('ix_repositories_name'), 'repositories', ['name'])

    # Create releases table
    op.create_table(
        'releases',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('repo_id', sa.String(), nullable=False),
        sa.Column('service', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('commit', sa.String(), nullable=False),
        sa.Column('branch', sa.String(), nullable=True, server_default='main'),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(), nullable=True, server_default='success'),
        sa.Column('risk_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('risk_level', sa.String(), nullable=True, server_default='Healthy'),
        sa.Column('deployment_duration', sa.Integer(), nullable=True),
        sa.Column('triggered_by', sa.String(), nullable=True),
        sa.Column('workflow_run_id', sa.String(), nullable=True),
        sa.Column('github_run_number', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['repo_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_release_deployed_at_status', 'releases', ['deployed_at', 'status'])
    op.create_index('idx_release_service_deployed_at', 'releases', ['service', 'deployed_at'])
    op.create_index(op.f('ix_releases_deployed_at'), 'releases', ['deployed_at'])
    op.create_index(op.f('ix_releases_repo_id'), 'releases', ['repo_id'])
    op.create_index(op.f('ix_releases_service'), 'releases', ['service'])
    op.create_index(op.f('ix_releases_workflow_run_id'), 'releases', ['workflow_run_id'], unique=True)

    # Create release_anomalies table
    op.create_table(
        'release_anomalies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('release_id', sa.String(), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('severity', sa.String(), nullable=True, server_default='low'),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('expected_value', sa.Float(), nullable=False),
        sa.Column('deviation', sa.Float(), nullable=False),
        sa.Column('anomaly_type', sa.String(), nullable=True, server_default='metric'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_release_anomaly_release_severity', 'release_anomalies', ['release_id', 'severity'])
    op.create_index(op.f('ix_release_anomalies_release_id'), 'release_anomalies', ['release_id'])
    op.create_index(op.f('ix_release_anomalies_timestamp'), 'release_anomalies', ['timestamp'])

    # Create release_incidents table
    op.create_table(
        'release_incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('release_id', sa.String(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('correlation_score', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['release_id'], ['releases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_release_incident_unique', 'release_incidents', ['release_id', 'incident_id'], unique=True)
    op.create_index(op.f('ix_release_incidents_id'), 'release_incidents', ['id'])
    op.create_index(op.f('ix_release_incidents_incident_id'), 'release_incidents', ['incident_id'])
    op.create_index(op.f('ix_release_incidents_release_id'), 'release_incidents', ['release_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('release_incidents')
    op.drop_table('release_anomalies')
    op.drop_table('releases')
    op.drop_table('repositories')
