"""add user isolation

Revision ID: 008
Revises: 007
Create Date: 2026-02-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # List of tables that need user_id column
    tables_to_update = [
        'repositories',
        'resources', 
        'incidents',
        'cloud_cost',
        'budgets',
        'cost_anomalies',
        'cost_agg',
        'deployments',
        'service_metrics',
        'metrics_anomalies',
        'services',
        'container_metrics',
        'pod_metrics',
        'recommendations'
    ]
    
    # Step 1: Add user_id columns (nullable initially)
    for table in tables_to_update:
        op.add_column(table, sa.Column('user_id', sa.Integer(), nullable=True))
        op.create_index(f'ix_{table}_user_id', table, ['user_id'])
    
    # Step 2: Handle orphaned data - delete records without user_id
    # In production, you might want to assign these to a system user instead
    for table in tables_to_update:
        op.execute(f"DELETE FROM {table} WHERE user_id IS NULL")
    
    # Step 3: Make user_id NOT NULL and add foreign keys
    for table in tables_to_update:
        op.alter_column(table, 'user_id', nullable=False)
        op.create_foreign_key(
            f'fk_{table}_user_id',
            table, 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )


def downgrade() -> None:
    tables_to_update = [
        'repositories',
        'resources',
        'incidents',
        'cloud_cost',
        'budgets',
        'cost_anomalies',
        'cost_agg',
        'deployments',
        'service_metrics',
        'metrics_anomalies',
        'services',
        'container_metrics',
        'pod_metrics',
        'recommendations'
    ]
    
    # Drop foreign keys, indexes, and columns
    for table in tables_to_update:
        op.drop_constraint(f'fk_{table}_user_id', table, type_='foreignkey')
        op.drop_index(f'ix_{table}_user_id', table)
        op.drop_column(table, 'user_id')
