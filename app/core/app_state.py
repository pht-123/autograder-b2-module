from __future__ import annotations

import logging
from dataclasses import dataclass

from app.clients.b3_client import B3Client
from app.clients.b4_client import B4Client
from app.core.config import Settings, load_settings
from app.core.logging import build_logger
from app.core.task_queue import AsyncTaskQueue
from app.modules.storage_module.file_storage import FileStorage
from app.repositories.submission_state_repo import SubmissionStateRepository
from app.services.evaluation_service import EvaluationService


@dataclass(slots=True)
class AppState:
    config: Settings
    logger: logging.Logger
    repo: SubmissionStateRepository
    storage: FileStorage
    b3: B3Client
    b4: B4Client
    queue: AsyncTaskQueue
    evaluator: EvaluationService


async def build_app_state() -> AppState:
    config = load_settings()
    logger = build_logger(config.log_dir)

    repo = SubmissionStateRepository()
    storage = FileStorage(config.code_storage_dir)

    b3 = B3Client(config.b3_base_url, timeout_s=config.http_timeout_s, retry_count=config.http_retry_count)
    b4 = B4Client(config.b4_base_url, timeout_s=config.http_timeout_s, retry_count=config.http_retry_count)

    evaluator = EvaluationService(repo=repo, b3=b3, b4=b4, logger=logger)
    queue = AsyncTaskQueue(worker_count=config.worker_count, handler=evaluator.handle_submission)
    await queue.start()

    logger.info("event=app_started worker_count=%s", config.worker_count)
    return AppState(
        config=config,
        logger=logger,
        repo=repo,
        storage=storage,
        b3=b3,
        b4=b4,
        queue=queue,
        evaluator=evaluator,
    )


async def shutdown_app_state(state: AppState) -> None:
    try:
        await state.queue.stop()
    finally:
        await state.b3.close()
        await state.b4.close()
