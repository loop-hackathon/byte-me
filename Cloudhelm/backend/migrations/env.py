"""
Alembic environment configuration.
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add parent directory to path to import backend modules
# Get the backend directory (parent of migrations)
backend_dir = os.path.dirname(os.path.dirname(__file__))
# Get the project root (parent of backend)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from backend.core.config import settings
from backend.core.db import Base

# Import all models so Alembic can detect them
from backend.models.user import User
from backend.models.cost import CloudCost, CostAggregate, Budget, CostAnomaly, Incident, Deployment
from backend.models.release import Repository, Release, ReleaseAnomaly, ReleaseIncident
from backend.models.resource import Resource, ResourceMetric, Recommendation
from backend.models.health import Service, ServiceMetric, MetricsAnomaly, ContainerMetric, PodMetric

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set sqlalchemy.url from settings
config.set_main_option('sqlalchemy.url', settings.database_url)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
