"""Methods for connecting and interacting with the database."""
import logging

import gino

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
