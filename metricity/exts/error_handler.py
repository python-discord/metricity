"""Handles errors emitted from commands."""

import discord
from botcore.utils import logging
from discord.ext import commands

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
            description=body
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, e: commands.errors.CommandError) -> None:
        """Provide generic command error handling."""
        if any(isinstance(e, suppressed_error) for suppressed_error in SUPPRESSED_ERRORS):
            log.debug(
                f"Command {ctx.command} invoked by {ctx.message.author} with error "
                f"{e.__class__.__name__}: {e}"
            )


async def setup(bot: commands.Bot) -> None:
    """Load the ErrorHandler cog."""
    await bot.add_cog(ErrorHandler(bot))
