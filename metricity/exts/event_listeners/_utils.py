import discord
from sqlalchemy.ext.asyncio import AsyncSession

from metricity import models


def insert_thread(thread: discord.Thread, sess: AsyncSession) -> None:
    """Insert the given thread to the database session."""
    sess.add(models.Thread(
        id=str(thread.id),
        parent_channel_id=str(thread.parent_id),
        name=thread.name,
        archived=thread.archived,
        auto_archive_duration=thread.auto_archive_duration,
        locked=thread.locked,
        type=thread.type.name,
        created_at=thread.created_at,
    ))


async def sync_message(message: discord.Message, sess: AsyncSession, *, from_thread: bool) -> None:
    """Sync the given message with the database."""
    if await sess.get(models.Message, str(message.id)):
        return

    args = {
        "id": str(message.id),
        "channel_id": str(message.channel.id),
        "author_id": str(message.author.id),
        "created_at": message.created_at,
    }

    if from_thread:
        thread = message.channel
        args["channel_id"] = str(thread.parent_id)
        args["thread_id"] = str(thread.id)

    sess.add(models.Message(**args))
