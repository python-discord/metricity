"""An ext to listen for message events and syncs them to the database."""

import discord
from discord.ext import commands
from sqlalchemy import update

from metricity.bot import Bot
from metricity.config import BotConfig
from metricity.database import async_session
from metricity.exts.event_listeners import _utils
from metricity.models import Message, User


class MessageListeners(commands.Cog):
    """Listen for message events and sync them to the database."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Add a message to the table when one is sent providing the author has accepted."""
        if not message.guild:
            return

        if message.author.bot:
            return

        if message.guild.id != BotConfig.guild_id:
            return

        if message.type in {discord.MessageType.thread_created, discord.MessageType.auto_moderation_action}:
            return

        await self.bot.sync_process_complete.wait()
        await self.bot.channel_sync_in_progress.wait()

        async with async_session() as sess:
            if not await sess.get(User, str(message.author.id)):
                return

            cat_id = message.channel.category.id if message.channel.category else None
            if cat_id in BotConfig.ignore_categories:
                return

            from_thread = isinstance(message.channel, discord.Thread)
            await _utils.sync_message(message, sess, from_thread=from_thread)

            await sess.commit()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, message: discord.RawMessageDeleteEvent) -> None:
        """If a message is deleted and we have a record of it set the is_deleted flag."""
        async with async_session() as sess:
            await sess.execute(update(Message).where(Message.id == str(message.message_id)).values(is_deleted=True))
            await sess.commit()

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, messages: discord.RawBulkMessageDeleteEvent) -> None:
        """If messages are deleted in bulk and we have a record of them set the is_deleted flag."""
        async with async_session() as sess:
            await sess.execute(update(Message).where(Message.id.in_(messages.message_ids)).values(is_deleted=True))
            await sess.commit()


async def setup(bot: Bot) -> None:
    """Load the MessageListeners cog."""
    await bot.add_cog(MessageListeners(bot))
