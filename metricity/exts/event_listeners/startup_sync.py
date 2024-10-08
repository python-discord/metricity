"""An ext to sync the guild when the bot starts up."""

import math
import time

import discord
from discord.ext import commands
from pydis_core.utils import logging, scheduling
from sqlalchemy import column, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import load_only

from metricity import models
from metricity.bot import Bot
from metricity.config import BotConfig
from metricity.database import async_session
from metricity.exts.event_listeners import _syncer_utils

log = logging.get_logger(__name__)


class StartupSyncer(commands.Cog):
    """Sync the guild on bot startup."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        scheduling.create_task(self.sync_guild())

    async def sync_guild(self) -> None:
        """Sync all channels and members in the guild."""
        await self.bot.wait_until_guild_available()

        guild = self.bot.get_guild(self.bot.guild_id)
        await _syncer_utils.sync_channels(self.bot, guild)

        log.info("Beginning thread archive state synchronisation process")
        await _syncer_utils.sync_thread_archive_state(guild)

        log.info("Beginning user synchronisation process")
        users = (
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
        )

        user_chunks = discord.utils.as_chunks(users, 500)
        created = 0
        updated = 0
        total_users = len(guild.members)

        log.info("Performing bulk upsert of %d rows in %d chunks", total_users, math.ceil(total_users / 500))

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

                log.info("User upsert: inserted %d rows, updated %d rows, done %d rows, %d rows remaining",
                         created, updated, created + updated, total_users - (created + updated))

            await sess.commit()

        log.info("User upsert complete")
        log.info("Beginning user in_guild sync")

        users_updated = 0
        guild_member_ids = {str(member.id) for member in guild.members}
        async with async_session() as sess:
            start = time.perf_counter()

            stmt = select(models.User).filter_by(in_guild=True).options(load_only(models.User.id))
            res = await sess.execute(stmt)
            in_guild_users = res.scalars()
            query = time.perf_counter()

            for user in in_guild_users:
                if user.id not in guild_member_ids:
                    users_updated += 1
                    user.in_guild = False
            proc = time.perf_counter()

            await sess.commit()
            end = time.perf_counter()

            log.debug(
                "in_guild sync: total time %fs, query %fs, processing %fs, commit %fs",
                end - start,
                query - start,
                proc - query,
                end - proc,
            )
        log.info("User in_guild sync updated %d users to be off guild", users_updated)
        log.info("User sync complete")

        self.bot.sync_process_complete.set()

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
    await bot.add_cog(StartupSyncer(bot))
