import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
# from sqlalchemy import create_engine # Keep if needed for specific cases

from alembic import context

# --- Project Specific Imports ---
# Add project root to sys.path to find the 'src' module
project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import Base from where it's defined (for autogenerate)
from src.services.database import Base

# Import the database URL from your settings file
from src.settings import DATABASE_URL
# --- End Project Specific Imports ---

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Configure target_metadata and sqlalchemy.url ---
# Set target_metadata for 'autogenerate' support
target_metadata = Base.metadata

# Set the sqlalchemy.url from settings, modifying for synchronous driver
if DATABASE_URL:
    # Replace asyncpg driver with psycopg2 for Alembic's synchronous operations
    sync_database_url = DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")
    config.set_main_option("sqlalchemy.url", sync_database_url)
else:
    # Handle case where DATABASE_URL might not be set (optional)
    print("WARNING: DATABASE_URL not found in settings, Alembic might use alembic.ini placeholder.")
    pass # Alembic will use the URL from alembic.ini if not set here
# --- End Configuration ---


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
    # Create engine using the configuration set above (sync URL)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool, # Use NullPool for migration script runs
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

