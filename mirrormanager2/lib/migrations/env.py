import logging
import os

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy_helpers.flask_ext import get_url_from_app

from mirrormanager2.app import create_app
from mirrormanager2.lib import read_config
from mirrormanager2.lib.model import BASE

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
alembic_config = context.config

# Don't touch the existing logging setup.
# logging.config.fileConfig(alembic_config.config_file_name)
logger = logging.getLogger("alembic.env")

try:
    url = get_url_from_app(create_app)
except OSError:
    # Usually because client_secrets.json can't be found, when run outside the frontend.
    config_path = os.environ.get("MM2_CONFIG", "/etc/mirrormanager/mirrormanager2.cfg")
    config = read_config(config_path)
    url = config["SQLALCHEMY_DATABASE_URI"]


alembic_config.set_main_option("sqlalchemy.url", url)
target_metadata = BASE.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(alembic_config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
