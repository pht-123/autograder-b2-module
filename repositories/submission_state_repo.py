from __future__ import annotations

import asyncio

from models.submission import SubmissionState
from modules.exception_module.errors import NotFoundError


class SubmissionStateRepository:
    def __init__(self) -> None:
        self._states: dict[str, SubmissionState] = {}
        self._lock = asyncio.Lock()

    async def save(self, state: SubmissionState) -> SubmissionState:
        async with self._lock:
            self._states[state.submission_id] = state
        return state

    async def get(self, submission_id: str) -> SubmissionState:
        async with self._lock:
            state = self._states.get(submission_id)
        if state is None:
            raise NotFoundError(f"submission_id={submission_id} not found")
        return state

