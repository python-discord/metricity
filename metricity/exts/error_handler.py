"""Handles errors emitted from commands."""

import discord
from discord.ext import commands
from pydis_core.utils import logging

log = logging.get_logger(__name__)


SUPPRESSED_ERRORS = (
    commands.errors.CommandNotFound,
    commands.errors.CheckFailure,
)


class ErrorHandler(commands.Cog):
    """Handles errors emitted from commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _get_error_embed(self, title: str, body: str) -> discord.Embed:
        """Return an embed that contains the exception."""
        return discord.Embed(
            title=title,
            colour=discord.Colour.red(),
            description=body,
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, e: commands.errors.CommandError) -> None:
        """Provide generic command error handling."""
        if isinstance(e, SUPPRESSED_ERRORS):
            log.debug(
                "Command %s invoked by %s with error %s: %s",
                ctx.invoked_with,
                ctx.message.author,
                e.__class__.__name__,
                e,
            )


async def setup(bot: commands.Bot) -> None:
    """Load the ErrorHandler cog."""
    await bot.add_cog(ErrorHandler(bot))
