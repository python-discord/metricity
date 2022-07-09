import discord

from metricity import models


async def insert_thread(thread: discord.Thread) -> None:
    """Insert the given thread to the database."""
    await models.Thread.create(
        id=str(thread.id),
        parent_channel_id=str(thread.parent_id),
        name=thread.name,
        archived=thread.archived,
        auto_archive_duration=thread.auto_archive_duration,
        locked=thread.locked,
        type=thread.type.name,
    )


async def sync_message(message: discord.Message, from_thread: bool) -> None:
    """Sync the given message with the database."""
    if await models.Message.get(str(message.id)):
        return

    if from_thread and not message.channel.parent:
        # This is a forum channel, not currently supported by Discord.py. Ignore it.
        return

    args = {
        "id": str(message.id),
        "channel_id": str(message.channel.id),
        "author_id": str(message.author.id),
        "created_at": message.created_at
    }

    if from_thread:
        thread = message.channel
        args["channel_id"] = str(thread.parent_id)
        args["thread_id"] = str(thread.id)
        if not await models.Thread.get(str(thread.id)):
            await insert_thread(thread)

    await models.Message.create(**args)
