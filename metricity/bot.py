"""Creating and configuring a Discord client for Metricity."""

import asyncio

from pydis_core import BotBase
from pydis_core.utils import logging, scheduling

from metricity import exts
from metricity.database import connect

log = logging.get_logger(__name__)


class Bot(BotBase):
    """A subclass of `pydis_core.BotBase` that implements bot-specific functions."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.sync_process_complete = asyncio.Event()
        self.channel_sync_in_progress = asyncio.Event()

    async def setup_hook(self) -> None:
        """Connect to db and load cogs."""
        await super().setup_hook()
        log.info(f"Metricity is online, logged in as {self.user}")
        await connect()
        scheduling.create_task(self.load_extensions(exts))

    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Log errors raised in event listeners rather than printing them to stderr."""
        log.exception(f"Unhandled exception in {event}.")
