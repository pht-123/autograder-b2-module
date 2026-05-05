from __future__ import annotations

"""
MailReceiver skeleton (IMAP polling + SMTP receipt).

This file is intentionally kept minimal for the homework deliverable:
- The business logic is defined by the docs, but real credentials and parsing rules
  depend on the deployment environment.
- The folder/module exists as a "deliverable module" from the weekly plan.
"""

import asyncio
import logging
from dataclasses import dataclass


@dataclass(slots=True)
class MailSettings:
    enabled: bool = False
    poll_interval_s: int = 10


class MailReceiver:
    def __init__(self, settings: MailSettings, logger: logging.Logger) -> None:
        self._settings = settings
        self._logger = logger
        self._stopping = asyncio.Event()
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if not self._settings.enabled or self._task is not None:
            return
        self._stopping.clear()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._stopping.set()
        if self._task is not None:
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None

    async def _loop(self) -> None:
        self._logger.info("event=mail_receiver_start")
        while not self._stopping.is_set():
            # TODO: connect to IMAP, fetch unseen mails, parse and submit.
            await asyncio.sleep(self._settings.poll_interval_s)
        self._logger.info("event=mail_receiver_stop")

