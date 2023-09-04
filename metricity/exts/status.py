"""Basic status commands to check the health of the bot."""
import datetime

import discord
from discord.ext import commands

from metricity.config import BotConfig

DESCRIPTIONS = (
    "Command processing time",
    "Last event received",
    "Discord API latency",
)
ROUND_LATENCY = 3
INTRO_MESSAGE = "Hello, I'm {name}. I insert all your data into a GDPR-compliant database."


class Status(commands.Cog):
    """Get the latency between the bot and Discord."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_socket_event_type(self, _: str) -> None:
        """Store the last event received as an int."""
        self.last_event_received = int(datetime.datetime.now(datetime.UTC).timestamp())

    @commands.command()
    @commands.has_any_role(BotConfig.staff_role_id)
    @commands.guild_only()
    async def status(self, ctx: commands.Context) -> None:
        """Respond with an embed with useful status info for debugging."""
        if ctx.guild.id != BotConfig.guild_id:
            return

        bot_ping = (datetime.datetime.now(datetime.UTC) - ctx.message.created_at).total_seconds() * 1000
        if bot_ping <= 0:
            bot_ping = "Your clock is out of sync, could not calculate ping."
        else:
            bot_ping = f"{bot_ping:.{ROUND_LATENCY}f} ms"

        discord_ping = f"{self.bot.latency * 1000:.{ROUND_LATENCY}f} ms"

        last_event = f"<t:{self.last_event_received}>"

        embed = discord.Embed(
            title="Status",
            description=INTRO_MESSAGE.format(name=ctx.guild.me.display_name),
        )

        for desc, latency in zip(DESCRIPTIONS, (bot_ping, last_event, discord_ping), strict=True):
            embed.add_field(name=desc, value=latency, inline=False)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Load the status extension."""
    await bot.add_cog(Status(bot))
