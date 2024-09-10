"""Database models used by Metricity for statistic collection."""

from datetime import UTC, datetime

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from metricity.database import TZDateTime


class Base(DeclarativeBase):
    """Base class for all database models."""


class Category(Base):
    """Database model representing a Discord category channel."""

    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    deleted: Mapped[bool] = mapped_column(default=False)


class Channel(Base):
    """Database model representing a Discord channel."""

    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    is_staff: Mapped[bool]
    deleted: Mapped[bool] = mapped_column(default=False)


class Thread(Base):
    """Database model representing a Thread channel."""

    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(primary_key=True)
    parent_channel_id: Mapped[str] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"))
    created_at = mapped_column(TZDateTime(), default=datetime.now(UTC))
    name: Mapped[str]
    archived: Mapped[bool]
    auto_archive_duration: Mapped[int]
    locked: Mapped[bool]
    type: Mapped[str] = mapped_column(index=True)


class User(Base):
    """Database model representing a Discord user."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    avatar_hash: Mapped[str] = mapped_column(nullable=True)
    guild_avatar_hash: Mapped[str] = mapped_column(nullable=True)
    joined_at = mapped_column(TZDateTime(), nullable=False)
    created_at = mapped_column(TZDateTime(), nullable=False)
    is_staff: Mapped[bool] = mapped_column(nullable=False)
    bot: Mapped[bool] = mapped_column(default=False)
    in_guild: Mapped[bool] = mapped_column(default=False)
    public_flags = mapped_column(JSON, default={})
    pending: Mapped[bool] = mapped_column(default=False)


class Message(Base):
    """Database model representing a message sent in a Discord server."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(primary_key=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    thread_id: Mapped[str | None] = mapped_column(ForeignKey("threads.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at = mapped_column(TZDateTime())
    is_deleted: Mapped[bool] = mapped_column(default=False)
    content_hash: Mapped[str] = mapped_column(nullable=True)
