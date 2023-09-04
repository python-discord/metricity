"""General utility functions and classes for Metricity."""

import logging
from datetime import UTC, datetime

import gino
from sqlalchemy.engine import Dialect
from sqlalchemy.types import DateTime, TypeDecorator

from metricity.config import DatabaseConfig

log = logging.getLogger(__name__)

db = gino.Gino()


def build_db_uri() -> str:
    """Use information from the config file to build a PostgreSQL URI."""
    if DatabaseConfig.uri:
        return DatabaseConfig.uri

    return (
        f"postgresql://{DatabaseConfig.username}:{DatabaseConfig.password}"
        f"@{DatabaseConfig.host}:{DatabaseConfig.port}/{DatabaseConfig.database}"
    )


async def connect() -> None:
    """Initiate a connection to the database."""
    log.info("Initiating connection to the database")
    await db.set_bind(build_db_uri())
    log.info("Database connection established")


class TZDateTime(TypeDecorator):
    """
    A db type that supports the use of aware datetimes in user-land.

    Source from SQLAlchemy docs:
    https://docs.sqlalchemy.org/en/14/core/custom_types.html#store-timezone-aware-timestamps-as-timezone-naive-utc

    Edited to include docstrings and type hints.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime, _dialect: Dialect) -> datetime:
        """Convert the value to aware before saving to db."""
        if value is not None:
            if not value.tzinfo:
                raise TypeError("tzinfo is required")
            value = value.astimezone(UTC).replace(tzinfo=None)
        return value

    def process_result_value(self, value: datetime, _dialect: Dialect) -> datetime:
        """Convert the value to aware before passing back to user-land."""
        if value is not None:
            value = value.replace(tzinfo=UTC)
        return value
