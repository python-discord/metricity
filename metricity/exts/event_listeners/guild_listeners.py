"""An ext to listen for guild (and guild channel) events and syncs them to the database."""

import discord
from discord.ext import commands
from pydis_core.utils import logging

from metricity.bot import Bot
from metricity.config import BotConfig
from metricity.exts.event_listeners import _syncer_utils

log = logging.get_logger(__name__)


class GuildListeners(commands.Cog):
    """Listen for guild (and guild channel) events and sync them to the database."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        """Sync the channels when one is created."""
        if channel.guild.id != BotConfig.guild_id:
            return

        await _syncer_utils.sync_channels(self.bot, channel.guild)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        """Set the deleted flag to true when a channel is deleted."""
        if channel.guild.id != BotConfig.guild_id:
            return

        await _syncer_utils.sync_channels(self.bot, channel.guild)

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        _before: discord.abc.GuildChannel,
        channel: discord.abc.GuildChannel,
    ) -> None:
        """Sync the channels when one is updated."""
        if channel.guild.id != BotConfig.guild_id:
            return

        await _syncer_utils.sync_channels(self.bot, channel.guild)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread) -> None:
        """Sync channels when a thread is created."""
        if thread.guild.id != BotConfig.guild_id:
            return

        await _syncer_utils.sync_channels(self.bot, thread.guild)

    @commands.Cog.listener()
    async def on_thread_update(self, _before: discord.Thread, thread: discord.Thread) -> None:
        """Sync the channels when one is updated."""
        if thread.guild.id != BotConfig.guild_id:
            return

        await _syncer_utils.sync_channels(self.bot, thread.guild)


async def setup(bot: Bot) -> None:
    """Load the GuildListeners cog."""
    await bot.add_cog(GuildListeners(bot))
