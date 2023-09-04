"""Ensures the metricity db exists before running migrations."""
import asyncio
from urllib.parse import SplitResult, urlsplit

import asyncpg

from metricity.database import build_db_uri


def parse_db_url(db_url: str) -> SplitResult:
    """Validate and split the given database url."""
    db_url_parts = urlsplit(db_url)
    if not all((
        db_url_parts.netloc,
        db_url_parts.username,
        db_url_parts.password,
    )):
        raise ValueError("The given db_url is not a valid PostgreSQL database URL.")
    return db_url_parts

async def create_db() -> None:
    """Create the Metricity database if it does not exist."""
    parts = parse_db_url(build_db_uri())
    try:
        await asyncpg.connect(
            host=parts.hostname,
            port=parts.port,
            user=parts.username,
            database=parts.path[1:],
            password=parts.password,
        )
    except asyncpg.InvalidCatalogNameError:
        print("Creating metricity database.") # noqa: T201
        sys_conn = await asyncpg.connect(
            database="template1",
            user=parts.username,
            host=parts.hostname,
            port=parts.port,
            password=parts.password,
        )

        await sys_conn.execute(
            f'CREATE DATABASE "{parts.path[1:] or "metricity"}" OWNER "{parts.username}"',
        )

        await sys_conn.close()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(create_db())
