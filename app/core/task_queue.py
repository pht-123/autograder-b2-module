from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


JobHandler = Callable[[str], Awaitable[None]]


class AsyncTaskQueue:
    """A lightweight in-process async queue for background evaluation tasks."""

    def __init__(self, worker_count: int, handler: JobHandler) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker_count = max(1, worker_count)
        self._handler = handler
        self._workers: list[asyncio.Task[None]] = []
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        if self._workers:
            return
        self._stopping.clear()
        for i in range(self._worker_count):
            self._workers.append(asyncio.create_task(self._worker_loop(i)))

    async def stop(self) -> None:
        self._stopping.set()
        # Wake up workers.
        for _ in self._workers:
            await self._queue.put("__STOP__")
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def enqueue(self, submission_id: str) -> None:
        await self._queue.put(submission_id)

    async def _worker_loop(self, worker_idx: int) -> None:
        while not self._stopping.is_set():
            submission_id = await self._queue.get()
            if submission_id == "__STOP__":
                return
            try:
                await self._handler(submission_id)
            finally:
                self._queue.task_done()

