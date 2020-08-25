"""Entry point for the Metricity application."""

from metricity.bot import bot
from metricity.config import BotConfig


def start() -> None:
    """Start the Metricity application."""
    bot.run(BotConfig.token)
