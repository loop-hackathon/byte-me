"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('provider_id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index('ix_users_provider_provider_id', 'users', ['provider', 'provider_id'], unique=True)
    
    # Create cloud_cost table
    op.create_table(
        'cloud_cost',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ts_date', sa.Date(), nullable=False),
        sa.Column('cloud', sa.String(), nullable=False),
        sa.Column('account_id', sa.String(), nullable=False),
        sa.Column('service', sa.String(), nullable=False),
        sa.Column('region', sa.String(), nullable=False),
        sa.Column('env', sa.String(), nullable=True),
        sa.Column('team', sa.String(), nullable=True),
        sa.Column('usage_type', sa.String(), nullable=True),
        sa.Column('cost_amount', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cloud_cost_id'), 'cloud_cost', ['id'], unique=False)
    op.create_index(op.f('ix_cloud_cost_ts_date'), 'cloud_cost', ['ts_date'], unique=False)
    op.create_index(op.f('ix_cloud_cost_cloud'), 'cloud_cost', ['cloud'], unique=False)
    op.create_index(op.f('ix_cloud_cost_service'), 'cloud_cost', ['service'], unique=False)
    op.create_index('idx_cloud_cost_date_cloud_service', 'cloud_cost', ['ts_date', 'cloud', 'service'], unique=False)
    
    # Create cost_agg table
    op.create_table(
        'cost_agg',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ts_date', sa.Date(), nullable=False),
        sa.Column('cloud', sa.String(), nullable=False),
        sa.Column('team', sa.String(), nullable=True),
        sa.Column('service', sa.String(), nullable=True),
        sa.Column('region', sa.String(), nullable=True),
        sa.Column('env', sa.String(), nullable=True),
        sa.Column('total_cost', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cost_agg_id'), 'cost_agg', ['id'], unique=False)
    op.create_index(op.f('ix_cost_agg_ts_date'), 'cost_agg', ['ts_date'], unique=False)
    op.create_index(op.f('ix_cost_agg_cloud'), 'cost_agg', ['cloud'], unique=False)
    op.create_index('idx_cost_agg_date_cloud_team', 'cost_agg', ['ts_date', 'cloud', 'team'], unique=False)
    op.create_index(
        'idx_cost_agg_unique',
        'cost_agg',
        ['ts_date', 'cloud', 'team', 'service', 'region', 'env'],
        unique=True
    )
    
    # Create budgets table
    op.create_table(
        'budgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team', sa.String(), nullable=False),
        sa.Column('service', sa.String(), nullable=True),
        sa.Column('monthly_budget_amount', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_budgets_id'), 'budgets', ['id'], unique=False)
    op.create_index(op.f('ix_budgets_team'), 'budgets', ['team'], unique=False)
    
    # Create cost_anomalies table
    op.create_table(
        'cost_anomalies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ts_date', sa.Date(), nullable=False),
        sa.Column('cloud', sa.String(), nullable=False),
        sa.Column('team', sa.String(), nullable=True),
        sa.Column('service', sa.String(), nullable=True),
        sa.Column('region', sa.String(), nullable=True),
        sa.Column('env', sa.String(), nullable=True),
        sa.Column('actual_cost', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column('expected_cost', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column('anomaly_score', sa.Float(), nullable=False),
        sa.Column('direction', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cost_anomalies_id'), 'cost_anomalies', ['id'], unique=False)
    op.create_index(op.f('ix_cost_anomalies_ts_date'), 'cost_anomalies', ['ts_date'], unique=False)
    op.create_index('idx_cost_anomaly_date_severity', 'cost_anomalies', ['ts_date', 'severity'], unique=False)


def downgrade() -> None:
    op.drop_table('cost_anomalies')
    op.drop_table('budgets')
    op.drop_table('cost_agg')
    op.drop_table('cloud_cost')
    op.drop_table('users')
