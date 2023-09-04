"""Metric collection for the Python Discord server."""

import asyncio
import logging
import os
from typing import TYPE_CHECKING

import coloredlogs
from pydis_core.utils import apply_monkey_patches

from metricity.config import PythonConfig

if TYPE_CHECKING:
    from metricity.bot import Bot

__version__ = "2.0.1"

# Set root log level
logging.basicConfig(level=PythonConfig.log_level)
coloredlogs.install(level=PythonConfig.log_level)

# Set Discord.py log level
logging.getLogger("discord.client").setLevel(PythonConfig.discord_log_level)

# On Windows, the selector event loop is required for aiodns.
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

apply_monkey_patches()

instance: "Bot" = None  # Global Bot instance.
