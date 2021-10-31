"""Database models used by Metricity for statistic collection."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.dialects.postgresql import insert

from metricity.database import db
from metricity.utils import TZDateTime


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
        nullable=True
    )
    is_staff = db.Column(db.Boolean, nullable=False)


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
    def bulk_upsert(cls: type, users: List[Dict[str, Any]]) -> Any:
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
            "pending"
        ]

        return qs.on_conflict_do_update(
            index_elements=[cls.id],
            set_={k: getattr(qs.excluded, k) for k in update_cols}
        ).returning(cls.__table__).gino.all()


class Message(db.Model):
    """Database model representing a message sent in a Discord server."""

    __tablename__ = "messages"

    id = db.Column(db.String, primary_key=True)
    channel_id = db.Column(
        db.String,
        db.ForeignKey("channels.id", ondelete="CASCADE"),
        index=True
    )
    author_id = db.Column(
        db.String,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    created_at = db.Column(TZDateTime(), default=datetime.now(timezone.utc))
    is_deleted = db.Column(db.Boolean, default=False)
