"""An ext to listen for guild (and guild channel) events and syncs them to the database."""

import discord
from discord.ext import commands
from pydis_core.utils import logging, scheduling
from sqlalchemy import column, update
from sqlalchemy.dialects.postgresql import insert

from metricity import models
from metricity.bot import Bot
from metricity.config import BotConfig
from metricity.database import async_session
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
        async with async_session() as sess:
            await sess.execute(update(models.User).values(in_guild=False))
            await sess.commit()

        users = [
            {
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
                "pending": user.pending,
            }
            for user in guild.members
        ]

        log.info("Performing bulk upsert of %d rows", len(users))

        user_chunks = discord.utils.as_chunks(users, 500)
        created = 0
        updated = 0

        async with async_session() as sess:
            for chunk in user_chunks:
                qs = insert(models.User).returning(column("xmax")).values(chunk)

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

                res = await sess.execute(qs.on_conflict_do_update(
                    index_elements=[models.User.id],
                    set_={k: getattr(qs.excluded, k) for k in update_cols},
                ))

                objs = list(res)

                created += [obj[0] == 0 for obj in objs].count(True)
                updated += [obj[0] != 0 for obj in objs].count(True)

                log.info("User upsert: inserted %d rows, updated %d rows, total %d rows",
                         created, updated, created + updated)

            await sess.commit()

        log.info("User upsert complete")

        self.bot.sync_process_complete.set()

    @staticmethod
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

    async def sync_channels(self, guild: discord.Guild) -> None:
        """Sync channels and categories with the database."""
        self.bot.channel_sync_in_progress.clear()

        log.info("Beginning category synchronisation process")

        async with async_session() as sess:
            for channel in guild.channels:
                if isinstance(channel, discord.CategoryChannel):
                    if existing_cat := await sess.get(models.Category, str(channel.id)):
                        existing_cat.name = channel.name
                    else:
                        sess.add(models.Category(id=str(channel.id), name=channel.name))

            await sess.commit()

        log.info("Category synchronisation process complete, synchronising channels")

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
                        ))

            await sess.commit()

        log.info("Channel synchronisation process complete, synchronising threads")

        async with async_session() as sess:
            for thread in guild.threads:
                if thread.parent and thread.parent.category:
                    if thread.parent.category.id in BotConfig.ignore_categories:
                        continue
                else:
                    # This is a forum channel, not currently supported by Discord.py. Ignore it.
                    continue

                if db_thread := await sess.get(models.Thread, str(thread.id)):
                    db_thread.name = thread.name
                    db_thread.archived = thread.archived
                    db_thread.auto_archive_duration = thread.auto_archive_duration
                    db_thread.locked = thread.locked
                    db_thread.type = thread.type.name
                else:
                    _utils.insert_thread(thread, sess)
            await sess.commit()

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
        channel: discord.abc.GuildChannel,
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
        log.info("Received guild available for %d", guild.id)

        if guild.id != BotConfig.guild_id:
            log.info("Guild was not the configured guild, discarding event")
            return

        await self.sync_guild()


async def setup(bot: Bot) -> None:
    """Load the GuildListeners cog."""
    await bot.add_cog(GuildListeners(bot))
