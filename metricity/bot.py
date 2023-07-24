"""Creating and configuring a Discord client for Metricity."""

import asyncio

from pydis_core import BotBase
from pydis_core.utils import logging

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
        log.info("Metricity is online, logged in as %s", self.user)
        await connect()
        await self.load_extensions(exts)

    async def on_error(self, event: str, *_args, **_kwargs) -> None:
        """Log errors raised in event listeners rather than printing them to stderr."""
        log.exception("Unhandled exception in %s", event)
