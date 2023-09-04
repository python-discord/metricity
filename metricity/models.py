"""Database models used by Metricity for statistic collection."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.dialects.postgresql import insert

from metricity.database import TZDateTime, db


class Category(db.Model):
    """Database model representing a Discord category channel."""

    __tablename__ = "categories"

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)


class Channel(db.Model):
    """Database model representing a Discord channel."""

    __tablename__ = "channels"

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    category_id = db.Column(
        db.String,
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
    )
    is_staff = db.Column(db.Boolean, nullable=False)


class Thread(db.Model):
    """Database model representing a Thread channel."""

    __tablename__ = "threads"

    id = db.Column(db.String, primary_key=True)
    parent_channel_id = db.Column(
        db.String,
        db.ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = db.Column(TZDateTime(), default=datetime.now(UTC))
    name = db.Column(db.String, nullable=False)
    archived = db.Column(db.Boolean, default=False, nullable=False)
    auto_archive_duration = db.Column(db.Integer, nullable=False)
    locked = db.Column(db.Boolean, default=False, nullable=False)
    type = db.Column(db.String, nullable=False, index=True)


class User(db.Model):
    """Database model representing a Discord user."""

    __tablename__ = "users"

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    avatar_hash = db.Column(db.String, nullable=True)
    guild_avatar_hash = db.Column(db.String, nullable=True)
    joined_at = db.Column(TZDateTime(), nullable=False)
    created_at = db.Column(TZDateTime(), nullable=False)
    is_staff = db.Column(db.Boolean, nullable=False)
    bot = db.Column(db.Boolean, default=False)
    in_guild = db.Column(db.Boolean, default=True)
    public_flags = db.Column(db.JSON, default={})
    pending = db.Column(db.Boolean, default=False)

    @classmethod
    def bulk_upsert(cls: type, users: list[dict[str, Any]]) -> Any:  # noqa: ANN401
        """Perform a bulk insert/update of the database to sync the user table."""
        qs = insert(cls.__table__).values(users)

        update_cols = [
            "name",
            "avatar_hash",
            "guild_avatar_hash",
            "joined_at",
            "is_staff",
            "bot",
            "in_guild",
            "public_flags",
            "pending",
        ]

        return qs.on_conflict_do_update(
            index_elements=[cls.id],
            set_={k: getattr(qs.excluded, k) for k in update_cols},
        ).returning(cls.__table__).gino.all()


class Message(db.Model):
    """Database model representing a message sent in a Discord server."""

    __tablename__ = "messages"

    id = db.Column(db.String, primary_key=True)
    channel_id = db.Column(
        db.String,
        db.ForeignKey("channels.id", ondelete="CASCADE"),
        index=True,
    )
    thread_id = db.Column(
        db.String,
        db.ForeignKey("threads.id", ondelete="CASCADE"),
        index=True,
    )
    author_id = db.Column(
        db.String,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    created_at = db.Column(TZDateTime(), default=datetime.now(UTC))
    is_deleted = db.Column(db.Boolean, default=False)
