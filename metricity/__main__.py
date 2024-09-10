"""Entry point for the Metricity application."""

import asyncio

import aiohttp
import discord
from discord.ext import commands

import metricity
from metricity.bot import Bot
from metricity.config import BotConfig


async def main() -> None:
    """Entry async method for starting the bot."""
    intents = discord.Intents(
        guilds=True,
        members=True,
        bans=False,
        emojis=False,
        integrations=False,
        webhooks=False,
        invites=False,
        voice_states=False,
        presences=False,
        messages=True,
        message_content=True,
        reactions=False,
        typing=False,
    )

    async with aiohttp.ClientSession() as session:
        metricity.instance = Bot(
            guild_id=BotConfig.guild_id,
            http_session=session,
            command_prefix=commands.when_mentioned,
            activity=discord.Game(f"Metricity {metricity.__version__}"),
            intents=intents,
            max_messages=None,
            allowed_mentions=None,
            allowed_roles=None,
            help_command=None,
        )
        async with metricity.instance as _bot:
            await _bot.start(BotConfig.token)


asyncio.run(main())
