"""Creating and configuring a Discord client for Metricity."""

import asyncio
import logging
from typing import Any, Generator, List

from asyncpg.exceptions import UniqueViolationError
from discord import (
    CategoryChannel,
    Game,
    Guild,
    Intents,
    Member,
    Message as DiscordMessage,
    MessageType,
    RawBulkMessageDeleteEvent,
    RawMessageDeleteEvent,
    Thread as ThreadChannel,
    VoiceChannel,
)
from discord.abc import Messageable
from discord.ext.commands import Bot

from metricity import __version__
from metricity.config import BotConfig
from metricity.database import connect, db
from metricity.models import Category, Channel, Message, Thread, User

log = logging.getLogger(__name__)

intents = Intents(
    guilds=True,
    members=True,
    bans=False,
    emojis=False,
    integrations=False,
    webhooks=False,
    invites=False,
    voice_states=False,
    presences=False,
    messages=True,
    reactions=False,
    typing=False
)


bot = Bot(
    command_prefix="",
    help_command=None,
    intents=intents,
    max_messages=None,
    activity=Game(f"Metricity {__version__}")
)

sync_process_complete = asyncio.Event()
channel_sync_in_progress = asyncio.Event()
db_ready = asyncio.Event()


async def insert_thread(thread: ThreadChannel) -> None:
    """Insert the given thread to the database."""
    await Thread.create(
        id=str(thread.id),
        parent_channel_id=str(thread.parent_id),
        name=thread.name,
        archived=thread.archived,
        auto_archive_duration=thread.auto_archive_duration,
        locked=thread.locked,
        type=thread.type.name,
    )


async def sync_channels(guild: Guild) -> None:
    """Sync channels and categories with the database."""
    channel_sync_in_progress.clear()

    log.info("Beginning category synchronisation process")

    for channel in guild.channels:
        if isinstance(channel, CategoryChannel):
            if db_cat := await Category.get(str(channel.id)):
                await db_cat.update(name=channel.name).apply()
            else:
                await Category.create(id=str(channel.id), name=channel.name)

    log.info("Category synchronisation process complete, synchronising channels")

    for channel in guild.channels:
        if channel.category:
            if channel.category.id in BotConfig.ignore_categories:
                continue

        if (
            not isinstance(channel, CategoryChannel) and
            not isinstance(channel, VoiceChannel)
        ):
            if db_chan := await Channel.get(str(channel.id)):
                await db_chan.update(
                    name=channel.name,
                    category_id=str(channel.category.id) if channel.category else None,
                    is_staff=(
                        channel.category
                        and channel.category.id in BotConfig.staff_categories
                    ),
                ).apply()
            else:
                await Channel.create(
                    id=str(channel.id),
                    name=channel.name,
                    category_id=str(channel.category.id) if channel.category else None,
                    is_staff=(
                        channel.category
                        and channel.category.id in BotConfig.staff_categories
                    ),
                )

    log.info("Channel synchronisation process complete, synchronising threads")

    for thread in guild.threads:
        if thread.parent and thread.parent.category:
            if thread.parent.category.id in BotConfig.ignore_categories:
                continue

        if db_thread := await Thread.get(str(thread.id)):
            await db_thread.update(
                name=thread.name,
                archived=thread.archived,
                auto_archive_duration=thread.auto_archive_duration,
                locked=thread.locked,
                type=thread.type.name,
            ).apply()
        else:
            await insert_thread(thread)
    channel_sync_in_progress.set()


async def sync_thread_archive_state(guild: Guild) -> None:
    """Sync the archive state of all threads in the database with the state in guild."""
    active_thread_ids = [str(thread.id) for thread in guild.threads]
    async with db.transaction() as tx:
        async for db_thread in tx.connection.iterate(Thread.query):
            await db_thread.update(archived=db_thread.id not in active_thread_ids).apply()


def gen_chunks(
    chunk_src: List[Any],
    chunk_size: int
) -> Generator[List[Any], None, List[Any]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(chunk_src), chunk_size):
        yield chunk_src[i:i + chunk_size]


@bot.event
async def on_ready() -> None:
    """Initiate tasks when the bot comes online."""
    log.info(f"Metricity is online, logged in as {bot.user}")
    await connect()
    db_ready.set()


@bot.event
async def on_guild_channel_create(channel: Messageable) -> None:
    """Sync the channels when one is created."""
    await db_ready.wait()

    if channel.guild.id != BotConfig.guild_id:
        return

    await sync_channels(channel.guild)


@bot.event
async def on_guild_channel_update(_before: Messageable, channel: Messageable) -> None:
    """Sync the channels when one is updated."""
    await db_ready.wait()

    if channel.guild.id != BotConfig.guild_id:
        return

    await sync_channels(channel.guild)


@bot.event
async def on_thread_update(_before: Messageable, thread: Messageable) -> None:
    """Sync the channels when one is updated."""
    await db_ready.wait()

    if thread.guild.id != BotConfig.guild_id:
        return

    await sync_channels(thread.guild)


@bot.event
async def on_guild_available(guild: Guild) -> None:
    """Synchronize the user table with the Discord users."""
    await db_ready.wait()

    log.info(f"Received guild available for {guild.id}")

    if guild.id != BotConfig.guild_id:
        return log.info("Guild was not the configured guild, discarding event")

    await sync_channels(guild)

    log.info("Beginning user synchronisation process")

    await User.update.values(in_guild=False).gino.status()

    users = []

    for user in guild.members:
        users.append({
            "id": str(user.id),
            "name": user.name,
            "avatar_hash": getattr(user.avatar, "key", None),
            "guild_avatar_hash": getattr(user.guild_avatar, "key", None),
            "joined_at": user.joined_at,
            "created_at": user.created_at,
            "is_staff": BotConfig.staff_role_id in [role.id for role in user.roles],
            "bot": user.bot,
            "in_guild": True,
            "public_flags": dict(user.public_flags),
            "pending": user.pending
        })

    log.info(f"Performing bulk upsert of {len(users)} rows")

    user_chunks = gen_chunks(users, 500)

    for chunk in user_chunks:
        log.info(f"Upserting chunk of {len(chunk)}")
        await User.bulk_upsert(chunk)

    log.info("User upsert complete")

    sync_process_complete.set()


@bot.event
async def on_member_join(member: Member) -> None:
    """On a user joining the server add them to the database."""
    await db_ready.wait()
    await sync_process_complete.wait()

    if member.guild.id != BotConfig.guild_id:
        return

    if db_user := await User.get(str(member.id)):
        await db_user.update(
            id=str(member.id),
            name=member.name,
            avatar_hash=getattr(member.avatar, "key", None),
            guild_avatar_hash=getattr(member.guild_avatar, "key", None),
            joined_at=member.joined_at,
            created_at=member.created_at,
            is_staff=BotConfig.staff_role_id in [role.id for role in member.roles],
            public_flags=dict(member.public_flags),
            pending=member.pending,
            in_guild=True
        ).apply()
    else:
        try:
            await User.create(
                id=str(member.id),
                name=member.name,
                avatar_hash=getattr(member.avatar, "key", None),
                guild_avatar_hash=getattr(member.guild_avatar, "key", None),
                joined_at=member.joined_at,
                created_at=member.created_at,
                is_staff=BotConfig.staff_role_id in [role.id for role in member.roles],
                public_flags=dict(member.public_flags),
                pending=member.pending,
                in_guild=True
            )
        except UniqueViolationError:
            pass


@bot.event
async def on_member_remove(member: Member) -> None:
    """On a user leaving the server mark in_guild as False."""
    await db_ready.wait()
    await sync_process_complete.wait()

    if member.guild.id != BotConfig.guild_id:
        return

    if db_user := await User.get(str(member.id)):
        await db_user.update(
            in_guild=False
        ).apply()


@bot.event
async def on_member_update(before: Member, member: Member) -> None:
    """When a member updates their profile, update the DB record."""
    await sync_process_complete.wait()

    if member.guild.id != BotConfig.guild_id:
        return

    # Joined at will be null if we are not ready to process events yet
    if not member.joined_at:
        return

    roles = set([role.id for role in member.roles])

    if db_user := await User.get(str(member.id)):
        if (
            db_user.name != member.name or
            db_user.avatar_hash != getattr(member.avatar, "key", None) or
            db_user.guild_avatar_hash != getattr(member.guild_avatar, "key", None) or
            BotConfig.staff_role_id in
            [role.id for role in member.roles] != db_user.is_staff
            or db_user.pending is not member.pending
        ):
            await db_user.update(
                id=str(member.id),
                name=member.name,
                avatar_hash=getattr(member.avatar, "key", None),
                guild_avatar_hash=getattr(member.guild_avatar, "key", None),
                joined_at=member.joined_at,
                created_at=member.created_at,
                is_staff=BotConfig.staff_role_id in roles,
                public_flags=dict(member.public_flags),
                in_guild=True,
                pending=member.pending
            ).apply()
    else:
        try:
            await User.create(
                id=str(member.id),
                name=member.name,
                avatar_hash=getattr(member.avatar, "key", None),
                guild_avatar_hash=getattr(member.guild_avatar, "key", None),
                joined_at=member.joined_at,
                created_at=member.created_at,
                is_staff=BotConfig.staff_role_id in roles,
                public_flags=dict(member.public_flags),
                in_guild=True,
                pending=member.pending
            )
        except UniqueViolationError:
            pass


@bot.event
async def on_message(message: DiscordMessage) -> None:
    """Add a message to the table when one is sent providing the author has accepted."""
    await db_ready.wait()

    if not message.guild:
        return

    if message.author.bot:
        return

    if message.guild.id != BotConfig.guild_id:
        return

    if message.type == MessageType.thread_created:
        return

    await sync_process_complete.wait()
    await channel_sync_in_progress.wait()

    if not await User.get(str(message.author.id)):
        return

    cat_id = message.channel.category.id if message.channel.category else None

    if cat_id in BotConfig.ignore_categories:
        return

    args = {
        "id": str(message.id),
        "channel_id": str(message.channel.id),
        "author_id": str(message.author.id),
        "created_at": message.created_at
    }

    if isinstance(message.channel, ThreadChannel):
        thread = message.channel
        args["channel_id"] = str(thread.parent_id)
        args["thread_id"] = str(thread.id)
        if not await Thread.get(str(thread.id)):
            await insert_thread(thread)

    await Message.create(**args)


@bot.event
async def on_raw_message_delete(message: RawMessageDeleteEvent) -> None:
    """If a message is deleted and we have a record of it set the is_deleted flag."""
    if message := await Message.get(str(message.message_id)):
        await message.update(is_deleted=True).apply()


@bot.event
async def on_raw_bulk_message_delete(messages: RawBulkMessageDeleteEvent) -> None:
    """If messages are deleted in bulk and we have a record of them set the is_deleted flag."""
    for message_id in messages.message_ids:
        if message := await Message.get(str(message_id)):
            await message.update(is_deleted=True).apply()
