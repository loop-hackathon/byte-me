"""add resource_efficiency table

Revision ID: 89b849f76ac3
Revises: 009
Create Date: 2026-03-12 04:28:09.668149

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '89b849f76ac3'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'resource_efficiency',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('service', sa.String(), nullable=True),
        sa.Column('cpu_util', sa.Float(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('efficiency_score', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resource_efficiency_id'), 'resource_efficiency', ['id'], unique=False)
    op.create_index(op.f('ix_resource_efficiency_service'), 'resource_efficiency', ['service'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resource_efficiency_service'), table_name='resource_efficiency')
    op.drop_index(op.f('ix_resource_efficiency_id'), table_name='resource_efficiency')
    op.drop_table('resource_efficiency')
