from __future__ import annotations

import asyncio

from clients.b4_client import B4Client
from models.submission import SubmissionState
from modules.exception_module.errors import NotFoundError


class SubmissionStateRepository:
    def __init__(self, b4: B4Client) -> None:
            self._states: dict[str, SubmissionState] = {}
            self._lock = asyncio.Lock()
            self._b4 = b4

    async def save(self, state: SubmissionState) -> SubmissionState:
            async with self._lock:
                self._states[state.submission_id] = state
            return state

    async def get(self, submission_id: str) -> SubmissionState:
            async with self._lock:
                state = self._states.get(submission_id)

            if state is not None:
                return state

            # 内存未命中，降级从 B4 持久源获取
            try:
                state = await self._b4.get_submission(submission_id)
                async with self._lock:
                    self._states[submission_id] = state
                return state
            except Exception:
                raise NotFoundError(f"submission_id={submission_id} not found in memory and B4")




