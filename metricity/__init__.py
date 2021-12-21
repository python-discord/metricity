"""Metric collection for the Python Discord server."""

import logging

import coloredlogs

from metricity.config import PythonConfig

__version__ = "1.3.0"

# Set root log level
logging.basicConfig(level=PythonConfig.log_level)
coloredlogs.install(level=PythonConfig.log_level)

# Set Discord.py log level
logging.getLogger("discord.client").setLevel(PythonConfig.discord_log_level)

# Gino has an obnoxiously loud log for all queries executed, not great when inserting
# tens of thousands of users, so we can disable that (it's just a SQLAlchemy logger)
logging.getLogger("gino.engine._SAEngine").setLevel(logging.WARNING)
