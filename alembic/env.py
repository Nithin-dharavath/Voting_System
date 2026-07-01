from logging.config import fileConfig
from urllib.parse import quote_plus

from sqlalchemy import create_engine, pool

from alembic import context  # type: ignore[attr-defined]
from config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = (
    f"mysql+mysqlconnector://{settings.db_user}:{quote_plus(settings.db_password)}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

target_metadata = None


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(database_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
