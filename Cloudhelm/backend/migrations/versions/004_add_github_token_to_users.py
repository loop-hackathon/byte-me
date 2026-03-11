"""add github token to users

Revision ID: 004
Revises: 003
Create Date: 2024-02-16

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add github_access_token column to users table
    op.add_column('users', sa.Column('github_access_token', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove github_access_token column from users table
    op.drop_column('users', 'github_access_token')
