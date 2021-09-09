"""Ensures the metricity db exists before running migrations."""
import os
from urllib.parse import SplitResult, urlsplit

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def parse_db_url(db_url: str) -> SplitResult:
    """Validate and split the given databse url."""
    db_url_parts = urlsplit(db_url)
    if not all((
        db_url_parts.hostname,
        db_url_parts.username,
        db_url_parts.password
    )):
        raise ValueError(
            "The given db_url is not a valid PostgreSQL database URL."
        )
    return db_url_parts


if __name__ == "__main__":
    database_parts = parse_db_url(os.environ["DATABASE_URI"])

    conn = psycopg2.connect(
        host=database_parts.hostname,
        port=database_parts.port,
        user=database_parts.username,
        password=database_parts.password
    )

    db_name = database_parts.path[1:] or "metricity"

    # Required to create a database in a .execute() call
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        if not exists:
            print("Creating metricity database.")
            cursor.execute(
                sql.SQL("CREATE DATABASE {dbname}").format(dbname=sql.Identifier(db_name))
            )
    conn.close()
