"""add resource efficiency models

Revision ID: 005
Revises: 004
Create Date: 2024-02-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Create resources table
    op.create_table(
        'resources',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('team', sa.String(), nullable=False),
        sa.Column('environment', sa.String(), nullable=False),
        sa.Column('waste_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_resources_id', 'resources', ['id'], unique=False)
    op.create_index('ix_resources_name', 'resources', ['name'], unique=False)
    op.create_index('ix_resources_team', 'resources', ['team'], unique=False)
    op.create_index('ix_resources_environment', 'resources', ['environment'], unique=False)
    op.create_index('idx_resource_team_env', 'resources', ['team', 'environment'], unique=False)
    op.create_index('idx_resource_waste_score', 'resources', ['waste_score'], unique=False)

    # Create resource_metrics table
    op.create_table(
        'resource_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('cpu_utilization', sa.Float(), nullable=False),
        sa.Column('memory_utilization', sa.Float(), nullable=False),
        sa.Column('disk_io', sa.Float(), nullable=True),
        sa.Column('network_io', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_resource_metrics_id', 'resource_metrics', ['id'], unique=False)
    op.create_index('ix_resource_metrics_resource_id', 'resource_metrics', ['resource_id'], unique=False)
    op.create_index('ix_resource_metrics_timestamp', 'resource_metrics', ['timestamp'], unique=False)
    op.create_index('idx_metric_resource_timestamp', 'resource_metrics', ['resource_id', 'timestamp'], unique=False)

    # Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('recommendation_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('potential_savings', sa.Float(), nullable=False),
        sa.Column('suggested_action', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True, server_default='0.8'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_recommendations_id', 'recommendations', ['id'], unique=False)
    op.create_index('ix_recommendations_resource_id', 'recommendations', ['resource_id'], unique=False)
    op.create_index('idx_recommendation_type', 'recommendations', ['recommendation_type'], unique=False)
    op.create_index('idx_recommendation_resource_type', 'recommendations', ['resource_id', 'recommendation_type'], unique=False)


def downgrade():
    # Drop recommendations table
    op.drop_index('idx_recommendation_resource_type', table_name='recommendations')
    op.drop_index('idx_recommendation_type', table_name='recommendations')
    op.drop_index('ix_recommendations_resource_id', table_name='recommendations')
    op.drop_index('ix_recommendations_id', table_name='recommendations')
    op.drop_table('recommendations')

    # Drop resource_metrics table
    op.drop_index('idx_metric_resource_timestamp', table_name='resource_metrics')
    op.drop_index('ix_resource_metrics_timestamp', table_name='resource_metrics')
    op.drop_index('ix_resource_metrics_resource_id', table_name='resource_metrics')
    op.drop_index('ix_resource_metrics_id', table_name='resource_metrics')
    op.drop_table('resource_metrics')

    # Drop resources table
    op.drop_index('idx_resource_waste_score', table_name='resources')
    op.drop_index('idx_resource_team_env', table_name='resources')
    op.drop_index('ix_resources_environment', table_name='resources')
    op.drop_index('ix_resources_team', table_name='resources')
    op.drop_index('ix_resources_name', table_name='resources')
    op.drop_index('ix_resources_id', table_name='resources')
    op.drop_table('resources')
