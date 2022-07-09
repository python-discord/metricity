"""Metric collection for the Python Discord server."""

import asyncio
import logging
import os
from typing import TYPE_CHECKING


import coloredlogs
from botcore.utils import apply_monkey_patches

from metricity.config import PythonConfig

if TYPE_CHECKING:
    from metricity.bot import Bot

__version__ = "1.4.0"

# Set root log level
logging.basicConfig(level=PythonConfig.log_level)
coloredlogs.install(level=PythonConfig.log_level)

# Set Discord.py log level
logging.getLogger("discord.client").setLevel(PythonConfig.discord_log_level)

# Gino has an obnoxiously loud log for all queries executed, not great when inserting
# tens of thousands of users, so we can disable that (it's just a SQLAlchemy logger)
logging.getLogger("gino.engine._SAEngine").setLevel(logging.WARNING)

# On Windows, the selector event loop is required for aiodns.
if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

apply_monkey_patches()

instance: "Bot" = None  # Global Bot instance.
