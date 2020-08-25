"""Creating and configuring a Discord client for Metricity."""

import asyncio
import logging
from typing import Any, Generator, List

from asyncpg.exceptions import UniqueViolationError
from discord import (
    CategoryChannel, Guild, Member,
    Message as DiscordMessage, VoiceChannel
)
from discord.abc import Messageable
from discord.ext.commands import Bot, Context

from metricity.config import BotConfig
from metricity.database import connect
from metricity.models import Category, Channel, Message, User

log = logging.getLogger(__name__)

bot = Bot(
    command_prefix=BotConfig.command_prefix
)

sync_process_complete = asyncio.Event()
channel_sync_in_progress = asyncio.Event()


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
                        True
                        if channel.category.id in BotConfig.staff_categories
                        else False
                    )
                ).apply()
            else:
                await Channel.create(
                    id=str(channel.id),
                    name=channel.name,
                    category_id=str(channel.category.id) if channel.category else None,
                    is_staff=(
                        True
                        if channel.category.id in BotConfig.staff_categories
                        else False
                    )
                )

    channel_sync_in_progress.set()


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


@bot.event
async def on_guild_channel_create(channel: Messageable) -> None:
    """Sync the channels when one is created."""
    if channel.guild.id != BotConfig.guild_id:
        return

    await sync_channels(channel.guild)


@bot.event
async def on_guild_channel_update(_before: Messageable, channel: Messageable) -> None:
    """Sync the channels when one is updated."""
    if channel.guild.id != BotConfig.guild_id:
        return

    await sync_channels(channel.guild)


@bot.event
async def on_guild_available(guild: Guild) -> None:
    """Synchronize the user table with the Discord users."""
    log.info(f"Received guild available for {guild.id}")

    if guild.id != BotConfig.guild_id:
        return log.info("Guild was not the configured guild, discarding event")

    await sync_channels(guild)

    log.info("Beginning user synchronisation process")

    await User.update.values(in_guild=False)

    users = []

    for user in guild.members:
        users.append({
            "id": str(user.id),
            "name": user.name,
            "avatar_hash": user.avatar,
            "joined_at": user.joined_at,
            "created_at": user.created_at,
            "is_staff": BotConfig.staff_role_id in [role.id for role in user.roles],
            "bot": user.bot,
            "in_guild": True
        })

    log.info(f"Performing bulk upsert of {len(users)} rows")

    user_chunks = gen_chunks(users, 2500)

    for chunk in user_chunks:
        log.info(f"Upserting chunk of {len(chunk)}")
        await User.bulk_upsert(chunk)

    log.info("User upsert complete")

    sync_process_complete.set()


@bot.event
async def on_member_join(member: Member) -> None:
    """On a user joining the server add them to the database."""
    await sync_process_complete.wait()

    if member.guild.id != BotConfig.guild_id:
        return

    if db_user := await User.get(str(member.id)):
        await db_user.update(
            id=str(member.id),
            name=member.name,
            avatar_hash=member.avatar,
            joined_at=member.joined_at,
            created_at=member.created_at,
            is_staff=BotConfig.staff_role_id in [role.id for role in member.roles]
        ).apply()
    else:
        try:
            await User.create(
                id=str(member.id),
                name=member.name,
                avatar_hash=member.avatar,
                joined_at=member.joined_at,
                created_at=member.created_at,
                is_staff=BotConfig.staff_role_id in [role.id for role in member.roles]
            )
        except UniqueViolationError:
            pass


@bot.event
async def on_member_remove(member: Member) -> None:
    """On a user leaving the server mark in_guild as False."""
    await sync_process_complete.wait()

    if member.guild.id != BotConfig.guild_id:
        return

    if db_user := await User.get(str(member.id)):
        await db_user.update(
            in_guild=False
        ).apply()


@bot.event
async def on_member_update(_before: Member, member: Member) -> None:
    """When a member updates their profile, update the DB record."""
    await sync_process_complete.wait()

    if member.guild.id != BotConfig.guild_id:
        return

    # Joined at will be null if we are not ready to process events yet
    if not member.joined_at:
        return

    if db_user := await User.get(str(member.id)):
        if (
            db_user.name != member.name or
            db_user.avatar_hash != member.avatar or
            BotConfig.staff_role_id in
            [role.id for role in member.roles] != db_user.is_staff
        ):
            await db_user.update(
                id=str(member.id),
                name=member.name,
                avatar_hash=member.avatar,
                joined_at=member.joined_at,
                created_at=member.created_at,
                is_staff=BotConfig.staff_role_id in [role.id for role in member.roles]
            ).apply()
    else:
        try:
            await User.create(
                id=str(member.id),
                name=member.name,
                avatar_hash=member.avatar,
                joined_at=member.joined_at,
                created_at=member.created_at,
                is_staff=BotConfig.staff_role_id in [role.id for role in member.roles]
            )
        except UniqueViolationError:
            pass


@bot.event
async def on_message(message: DiscordMessage) -> None:
    """Add a message to the table when one is sent providing the author has accepted."""
    if message.channel.id == BotConfig.bot_commands_channel:
        await bot.process_commands(message)

    if not message.guild:
        return

    if message.guild.id != BotConfig.guild_id:
        return

    await sync_process_complete.wait()
    await channel_sync_in_progress.wait()

    if author := await User.get(str(message.author.id)):
        if author.opt_out:
            return
    else:
        return

    cat_id = message.channel.category.id if message.channel.category else None

    if cat_id in BotConfig.ignore_categories:
        return

    await Message.create(
        id=str(message.id),
        channel_id=str(message.channel.id),
        author_id=str(message.author.id),
        created_at=message.created_at
    )


@bot.command()
async def opt_in(ctx: Context) -> None:
    """Opt-in to the server analytics system."""
    user = await User.get(str(ctx.author.id))

    if not user:
        return await ctx.send(
            f"Sorry {ctx.author.mention}, I don't have a record for you yet"
            " which probably means you joined recently enough to have missed"
            " the user synchronisation. Please check back soon or contact"
            " `joe#1337` for additional help."
        )

    await user.update(opt_out=False).apply()

    await ctx.send("Your preferences have been updated.")


@bot.command()
async def opt_out(ctx: Context) -> None:
    """
    Opt-out to the server analytics system.

    This only disables message reporting, user information is kept
    in accordance with our privacy policy.
    """
    user = await User.get(str(ctx.author.id))

    if not user:
        return await ctx.send(
            f"Sorry {ctx.author.mention}, I don't have a record for you yet"
            " which probably means you joined recently enough to have missed"
            " the user synchronisation. Please check back soon or contact"
            " `joe#1337` for additional help."
        )

    await user.update(opt_out=True).apply()

    await ctx.send("Your preferences have been updated.")
