"""add health monitoring models

Revision ID: 006
Revises: 005
Create Date: 2024-02-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Create services table
    op.create_table(
        'services',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_name', sa.String(length=255), nullable=False),
        sa.Column('service_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_services_id', 'services', ['id'], unique=False)
    op.create_index('ix_services_service_name', 'services', ['service_name'], unique=True)

    # Create service_metrics table
    op.create_table(
        'service_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_name', sa.String(length=255), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('request_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('error_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('latency_p50', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('latency_p95', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('latency_p99', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('cpu_usage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('memory_usage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('restart_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pod_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('service_name', 'timestamp', name='uq_service_metrics_service_timestamp')
    )
    op.create_index('ix_service_metrics_id', 'service_metrics', ['id'], unique=False)
    op.create_index('ix_service_metrics_service_name', 'service_metrics', ['service_name'], unique=False)
    op.create_index('ix_service_metrics_timestamp', 'service_metrics', ['timestamp'], unique=False)
    op.create_index('idx_service_metrics_service_timestamp', 'service_metrics', ['service_name', 'timestamp'], unique=False)

    # Create metrics_anomalies table
    op.create_table(
        'metrics_anomalies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_name', sa.String(length=255), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('anomaly_type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('anomaly_score', sa.Float(), nullable=False),
        sa.Column('affected_metrics', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_metrics_anomalies_id', 'metrics_anomalies', ['id'], unique=False)
    op.create_index('ix_metrics_anomalies_service_name', 'metrics_anomalies', ['service_name'], unique=False)
    op.create_index('ix_metrics_anomalies_timestamp', 'metrics_anomalies', ['timestamp'], unique=False)
    op.create_index('ix_metrics_anomalies_severity', 'metrics_anomalies', ['severity'], unique=False)
    op.create_index('idx_metrics_anomalies_service_severity', 'metrics_anomalies', ['service_name', 'severity'], unique=False)
    op.create_index('idx_metrics_anomalies_timestamp_severity', 'metrics_anomalies', ['timestamp', 'severity'], unique=False)

    # Create container_metrics table
    op.create_table(
        'container_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('container_id', sa.String(length=255), nullable=False),
        sa.Column('container_name', sa.String(length=255), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cpu_percent', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('memory_usage_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('memory_percent', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('network_rx_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('network_tx_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('disk_read_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('disk_write_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pids', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_container_metrics_id', 'container_metrics', ['id'], unique=False)
    op.create_index('ix_container_metrics_container_id', 'container_metrics', ['container_id'], unique=False)
    op.create_index('ix_container_metrics_container_name', 'container_metrics', ['container_name'], unique=False)
    op.create_index('ix_container_metrics_timestamp', 'container_metrics', ['timestamp'], unique=False)
    op.create_index('idx_container_metrics_container_timestamp', 'container_metrics', ['container_id', 'timestamp'], unique=False)
    op.create_index('idx_container_metrics_name_timestamp', 'container_metrics', ['container_name', 'timestamp'], unique=False)

    # Create pod_metrics table
    op.create_table(
        'pod_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pod_name', sa.String(length=255), nullable=False),
        sa.Column('namespace', sa.String(length=255), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('phase', sa.String(length=50), nullable=False),
        sa.Column('ready_containers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_containers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('restart_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('node_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pod_metrics_id', 'pod_metrics', ['id'], unique=False)
    op.create_index('ix_pod_metrics_pod_name', 'pod_metrics', ['pod_name'], unique=False)
    op.create_index('ix_pod_metrics_namespace', 'pod_metrics', ['namespace'], unique=False)
    op.create_index('ix_pod_metrics_timestamp', 'pod_metrics', ['timestamp'], unique=False)
    op.create_index('idx_pod_metrics_pod_timestamp', 'pod_metrics', ['pod_name', 'timestamp'], unique=False)
    op.create_index('idx_pod_metrics_namespace_timestamp', 'pod_metrics', ['namespace', 'timestamp'], unique=False)
    op.create_index('idx_pod_metrics_namespace_pod', 'pod_metrics', ['namespace', 'pod_name'], unique=False)


def downgrade():
    # Drop pod_metrics table
    op.drop_index('idx_pod_metrics_namespace_pod', table_name='pod_metrics')
    op.drop_index('idx_pod_metrics_namespace_timestamp', table_name='pod_metrics')
    op.drop_index('idx_pod_metrics_pod_timestamp', table_name='pod_metrics')
    op.drop_index('ix_pod_metrics_timestamp', table_name='pod_metrics')
    op.drop_index('ix_pod_metrics_namespace', table_name='pod_metrics')
    op.drop_index('ix_pod_metrics_pod_name', table_name='pod_metrics')
    op.drop_index('ix_pod_metrics_id', table_name='pod_metrics')
    op.drop_table('pod_metrics')

    # Drop container_metrics table
    op.drop_index('idx_container_metrics_name_timestamp', table_name='container_metrics')
    op.drop_index('idx_container_metrics_container_timestamp', table_name='container_metrics')
    op.drop_index('ix_container_metrics_timestamp', table_name='container_metrics')
    op.drop_index('ix_container_metrics_container_name', table_name='container_metrics')
    op.drop_index('ix_container_metrics_container_id', table_name='container_metrics')
    op.drop_index('ix_container_metrics_id', table_name='container_metrics')
    op.drop_table('container_metrics')

    # Drop metrics_anomalies table
    op.drop_index('idx_metrics_anomalies_timestamp_severity', table_name='metrics_anomalies')
    op.drop_index('idx_metrics_anomalies_service_severity', table_name='metrics_anomalies')
    op.drop_index('ix_metrics_anomalies_severity', table_name='metrics_anomalies')
    op.drop_index('ix_metrics_anomalies_timestamp', table_name='metrics_anomalies')
    op.drop_index('ix_metrics_anomalies_service_name', table_name='metrics_anomalies')
    op.drop_index('ix_metrics_anomalies_id', table_name='metrics_anomalies')
    op.drop_table('metrics_anomalies')

    # Drop service_metrics table
    op.drop_index('idx_service_metrics_service_timestamp', table_name='service_metrics')
    op.drop_index('ix_service_metrics_timestamp', table_name='service_metrics')
    op.drop_index('ix_service_metrics_service_name', table_name='service_metrics')
    op.drop_index('ix_service_metrics_id', table_name='service_metrics')
    op.drop_table('service_metrics')

    # Drop services table
    op.drop_index('ix_services_service_name', table_name='services')
    op.drop_index('ix_services_id', table_name='services')
    op.drop_table('services')
