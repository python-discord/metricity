"""Adds a message sync command to Metricity."""
import datetime

import discord
from discord.ext import commands

from metricity.bot import sync_message
from metricity.config import BotConfig


async def sync_messages(interaction_message: discord.Message, from_epoch: int, to_epoch: int) -> None:
    """Ensure all messages between the two epochs exist in the database, inserting if them missing."""
    guild = interaction_message.guild
    from_date = datetime.datetime.fromtimestamp(from_epoch, tz=datetime.timezone.utc)
    to_date = datetime.datetime.fromtimestamp(to_epoch, tz=datetime.timezone.utc)

    threads = guild.threads
    for channel in guild.channels:
        if isinstance(channel, discord.TextChannel):
            async for message in channel.history(before=to_date, after=from_date, limit=None):
                await sync_message(message, from_thread=False)

            threads += await channel.archived_threads().flatten()

    await interaction_message.edit(":incoming_envelope: Synchronising messages from threads...")

    for thread in threads:
        async for message in thread.history(before=to_date, after=from_date, limit=None):
            await sync_message(message, from_thread=True)


class ConfirmSync(discord.ui.View):
    """A confirmation view for synchronising mesages."""

    def __init__(self, context: commands.Context, date_range: tuple[int, int]) -> None:
        super().__init__()
        self.context = context
        self.from_epoch, self.to_epoch, = date_range

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check the interactor is authorised."""
        if interaction.user.id == self.context.author.id:
            return True

        await interaction.response.send_message(
            ":no_entry_sign: You are not authorized to perform this action.",
            ephemeral=True,
        )

        return False

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, row=0)
    async def confirm(self, _button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Redeploy the specified service."""
        await interaction.message.edit(":incoming_envelope: Synchronising messages from channels...", view=None)

        await sync_messages(interaction.message, self.from_epoch, self.to_epoch)

        await interaction.message.edit(":white_check_mark: Synchronisation complete!", view=None)

        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey, row=0)
    async def cancel(self, _button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """Logic for if the deployment is not approved."""
        await interaction.message.edit(":x: Synchronisation aborted", view=None)
        self.stop()


class MessageSyncer(commands.Cog):
    """Ensure data integrity by syncing all messages for a given time period."""

    @commands.command(name="sync_messages", aliases=("message_sync",))
    @commands.is_owner()
    @commands.guild_only()
    async def sync_messages_command(self, ctx: commands.Context, from_epoch: int, to_epoch: int) -> None:
        """
        Sync all messages within the given time period.

        Both from_epoch and to_epoch are interpreted as UNIX timestamps.
        """
        if ctx.guild.id != BotConfig.guild_id:
            return

        if from_epoch > to_epoch:
            from_epoch, to_epoch = to_epoch, from_epoch

        confirmation = ConfirmSync(ctx, (from_epoch, to_epoch))
        message = await ctx.send(
            f"Are you sure you want to sync messages from <t:{from_epoch}> to <t:{to_epoch}>?",
            view=confirmation,
        )

        if await confirmation.wait():
            await message.edit(":x: Synchronisation aborted, you were too slow.", view=None)


def setup(bot: commands.Bot) -> None:
    """Load the message sync extension."""
    bot.add_cog(MessageSyncer())
