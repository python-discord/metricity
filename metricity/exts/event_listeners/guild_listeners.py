"""An ext to listen for guild (and guild channel) events and syncs them to the database."""

import discord
from discord.ext import commands
from pydis_core.utils import logging, scheduling

from metricity import models
from metricity.bot import Bot
from metricity.config import BotConfig
from metricity.database import db
from metricity.exts.event_listeners import _utils

log = logging.get_logger(__name__)


class GuildListeners(commands.Cog):
    """Listen for guild (and guild channel) events and sync them to the database."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        scheduling.create_task(self.sync_guild())

    async def sync_guild(self) -> None:
        """Sync all channels and members in the guild."""
        await self.bot.wait_until_guild_available()

        guild = self.bot.get_guild(self.bot.guild_id)
        await self.sync_channels(guild)

        log.info("Beginning thread archive state synchronisation process")
        await self.sync_thread_archive_state(guild)

        log.info("Beginning user synchronisation process")
        await models.User.update.values(in_guild=False).gino.status()

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

        user_chunks = discord.utils.as_chunks(users, 500)

        for chunk in user_chunks:
            log.info(f"Upserting chunk of {len(chunk)}")
            await models.User.bulk_upsert(chunk)

        log.info("User upsert complete")

        self.bot.sync_process_complete.set()

    @staticmethod
    async def sync_thread_archive_state(guild: discord.Guild) -> None:
        """Sync the archive state of all threads in the database with the state in guild."""
        active_thread_ids = [str(thread.id) for thread in guild.threads]
        async with db.transaction() as tx:
            async for db_thread in tx.connection.iterate(models.Thread.query):
                await db_thread.update(archived=db_thread.id not in active_thread_ids).apply()

    async def sync_channels(self, guild: discord.Guild) -> None:
        """Sync channels and categories with the database."""
        self.bot.channel_sync_in_progress.clear()

        log.info("Beginning category synchronisation process")

        for channel in guild.channels:
            if isinstance(channel, discord.CategoryChannel):
                if db_cat := await models.Category.get(str(channel.id)):
                    await db_cat.update(name=channel.name).apply()
                else:
                    await models.Category.create(id=str(channel.id), name=channel.name)

        log.info("Category synchronisation process complete, synchronising channels")

        for channel in guild.channels:
            if channel.category:
                if channel.category.id in BotConfig.ignore_categories:
                    continue

            if not isinstance(channel, discord.CategoryChannel):
                category_id = str(channel.category.id) if channel.category else None
                # Cast to bool so is_staff is False if channel.category is None
                is_staff = channel.id in BotConfig.staff_channels or bool(
                    channel.category and channel.category.id in BotConfig.staff_categories
                )
                if db_chan := await models.Channel.get(str(channel.id)):
                    await db_chan.update(
                        name=channel.name,
                        category_id=category_id,
                        is_staff=is_staff,
                    ).apply()
                else:
                    await models.Channel.create(
                        id=str(channel.id),
                        name=channel.name,
                        category_id=category_id,
                        is_staff=is_staff,
                    )

        log.info("Channel synchronisation process complete, synchronising threads")

        for thread in guild.threads:
            if thread.parent and thread.parent.category:
                if thread.parent.category.id in BotConfig.ignore_categories:
                    continue
            else:
                # This is a forum channel, not currently supported by Discord.py. Ignore it.
                continue

            if db_thread := await models.Thread.get(str(thread.id)):
                await db_thread.update(
                    name=thread.name,
                    archived=thread.archived,
                    auto_archive_duration=thread.auto_archive_duration,
                    locked=thread.locked,
                    type=thread.type.name,
                ).apply()
            else:
                await _utils.insert_thread(thread)

        log.info("Thread synchronisation process complete, finished synchronising guild.")
        self.bot.channel_sync_in_progress.set()

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        """Sync the channels when one is created."""
        if channel.guild.id != BotConfig.guild_id:
            return

        await self.sync_channels(channel.guild)

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        _before: discord.abc.GuildChannel,
        channel: discord.abc.GuildChannel
    ) -> None:
        """Sync the channels when one is updated."""
        if channel.guild.id != BotConfig.guild_id:
            return

        await self.sync_channels(channel.guild)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread) -> None:
        """Sync channels when a thread is created."""
        if thread.guild.id != BotConfig.guild_id:
            return

        await self.sync_channels(thread.guild)

    @commands.Cog.listener()
    async def on_thread_update(self, _before: discord.Thread, thread: discord.Thread) -> None:
        """Sync the channels when one is updated."""
        if thread.guild.id != BotConfig.guild_id:
            return

        await self.sync_channels(thread.guild)

    @commands.Cog.listener()
    async def on_guild_available(self, guild: discord.Guild) -> None:
        """Synchronize the user table with the Discord users."""
        log.info(f"Received guild available for {guild.id}")

        if guild.id != BotConfig.guild_id:
            log.info("Guild was not the configured guild, discarding event")
            return

        await self.sync_guild()


async def setup(bot: Bot) -> None:
    """Load the GuildListeners cog."""
    await bot.add_cog(GuildListeners(bot))
