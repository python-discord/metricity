import binascii
import hashlib

import discord
from pydis_core.utils import logging
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from metricity import models
from metricity.bot import Bot
from metricity.config import BotConfig
from metricity.database import async_session

log = logging.get_logger(__name__)


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

    hash_ctx = hashlib.md5() # noqa: S324
    hash_ctx.update(message.content.encode())
    digest = hash_ctx.digest()
    digest_encoded = binascii.hexlify(digest).decode()

    args = {
        "id": str(message.id),
        "channel_id": str(message.channel.id),
        "author_id": str(message.author.id),
        "created_at": message.created_at,
        "content_hash": digest_encoded,
    }

    if from_thread:
        thread = message.channel
        args["channel_id"] = str(thread.parent_id)
        args["thread_id"] = str(thread.id)

    sess.add(models.Message(**args))


async def sync_channels(bot: Bot, guild: discord.Guild) -> None:
    """Sync channels and categories with the database."""
    bot.channel_sync_in_progress.clear()

    log.info("Beginning category synchronisation process")

    async with async_session() as sess:
        for channel in guild.channels:
            if isinstance(channel, discord.CategoryChannel):
                if existing_cat := await sess.get(models.Category, str(channel.id)):
                    existing_cat.name = channel.name
                else:
                    sess.add(models.Category(id=str(channel.id), name=channel.name, deleted=False))

        await sess.commit()

    log.info("Category synchronisation process complete, synchronising deleted categories")

    async with async_session() as sess:
        await sess.execute(
            update(models.Category)
            .where(~models.Category.id.in_(
                [str(channel.id) for channel in guild.channels if isinstance(channel, discord.CategoryChannel)],
            ))
            .values(deleted=True),
        )
        await sess.commit()

    log.info("Deleted category synchronisation process complete, synchronising channels")

    async with async_session() as sess:
        for channel in guild.channels:
            if channel.category and channel.category.id in BotConfig.ignore_categories:
                continue

            if not isinstance(channel, discord.CategoryChannel):
                category_id = str(channel.category.id) if channel.category else None
                # Cast to bool so is_staff is False if channel.category is None
                is_staff = channel.id in BotConfig.staff_channels or bool(
                    channel.category and channel.category.id in BotConfig.staff_categories,
                )
                if db_chan := await sess.get(models.Channel, str(channel.id)):
                    db_chan.name = channel.name
                else:
                    sess.add(models.Channel(
                        id=str(channel.id),
                        name=channel.name,
                        category_id=category_id,
                        is_staff=is_staff,
                        deleted=False,
                    ))

        await sess.commit()

    log.info("Channel synchronisation process complete, synchronising deleted channels")

    async with async_session() as sess:
        await sess.execute(
            update(models.Channel)
            .where(~models.Channel.id.in_([str(channel.id) for channel in guild.channels]))
            .values(deleted=True),
        )
        await sess.commit()

    log.info("Deleted channel synchronisation process complete, synchronising threads")

    async with async_session() as sess:
        for thread in guild.threads:
            if thread.parent and thread.parent.category and thread.parent.category.id in BotConfig.ignore_categories:
                continue

            if db_thread := await sess.get(models.Thread, str(thread.id)):
                db_thread.name = thread.name
                db_thread.archived = thread.archived
                db_thread.auto_archive_duration = thread.auto_archive_duration
                db_thread.locked = thread.locked
                db_thread.type = thread.type.name
            else:
                insert_thread(thread, sess)
        await sess.commit()

    log.info("Thread synchronisation process complete, synchronising deleted threads")
    await sync_thread_archive_state(guild)
    log.info("Thread synchronisation process complete, finished synchronising guild.")
    bot.channel_sync_in_progress.set()


async def sync_thread_archive_state(guild: discord.Guild) -> None:
    """Sync the archive state of all threads in the database with the state in guild."""
    active_thread_ids = [str(thread.id) for thread in guild.threads]

    async with async_session() as sess:
        await sess.execute(
            update(models.Thread)
            .where(models.Thread.id.in_(active_thread_ids))
            .values(archived=False),
        )
        await sess.execute(
            update(models.Thread)
            .where(~models.Thread.id.in_(active_thread_ids))
            .values(archived=True),
        )
        await sess.commit()
