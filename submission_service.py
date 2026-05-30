from __future__ import annotations

import logging
import uuid

from core.config import Settings
from core.task_queue import AsyncTaskQueue
from models.submission import SubmissionCreateRequest, SubmissionCreateResponse, SubmissionState
from modules.exception_module.errors import ValidationError
from modules.storage_module.file_storage import FileStorage
from repositories.submission_state_repo import SubmissionStateRepository


class SubmissionService:
    def __init__(
        self,
        config: Settings,
        repo: SubmissionStateRepository,
        storage: FileStorage,
        queue: AsyncTaskQueue,
        logger: logging.Logger,
    ) -> None:
        self._config = config
        self._repo = repo
        self._storage = storage
        self._queue = queue
        self._logger = logger

    async def create_submission(self, req: SubmissionCreateRequest) -> SubmissionCreateResponse:
        if req.language.lower() not in ("python", "shell"):
            raise ValidationError(f"unsupported language: {req.language}, only python/shell allowed")


        submission_id = str(uuid.uuid4())

        code_path = self._storage.build_code_path(
            assignment_id=req.assignment_id,
            question_id=req.question_id,
            student_user_id=req.student_user_id,
            submission_id=submission_id,
            language=req.language,
        )
        self._storage.save_code(code_path, req.code)

        state = SubmissionState(
            submission_id=submission_id,
            student_user_id=req.student_user_id,
            question_id=req.question_id,
            assignment_id=req.assignment_id,
            code_path=str(code_path),
            status="PENDING",
        )
        await self._repo.save(state)

        await self._queue.enqueue(submission_id)
        self._logger.info("event=submission_created submission_id=%s path=%s", submission_id, str(code_path))
        return SubmissionCreateResponse(submission_id=submission_id, status="PENDING")
