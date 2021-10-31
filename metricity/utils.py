"""General utility functions and classes for Metricity."""
from datetime import datetime, timezone

from sqlalchemy.engine import Dialect
from sqlalchemy.types import DateTime, TypeDecorator


class TZDateTime(TypeDecorator):
    """
    A db type that supports the use of aware datetimes in user-land.

    Source from SQLAlchemy docs:
    https://docs.sqlalchemy.org/en/14/core/custom_types.html#store-timezone-aware-timestamps-as-timezone-naive-utc

    Editted to include docstrings and type hints.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime, dialect: Dialect) -> datetime:
        """Convert the value to aware before saving to db."""
        if value is not None:
            if not value.tzinfo:
                raise TypeError("tzinfo is required")
            value = value.astimezone(timezone.utc).replace(
                tzinfo=None
            )
        return value

    def process_result_value(self, value: datetime, dialect: Dialect) -> datetime:
        """Convert the value to aware before passing back to user-land."""
        if value is not None:
            value = value.replace(tzinfo=timezone.utc)
        return value
