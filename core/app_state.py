from __future__ import annotations

import logging
from dataclasses import dataclass

from clients.b3_client import B3Client
from clients.b4_client import B4Client
from core.config import Settings, load_settings
from core.logging import build_logger
from core.task_queue import AsyncTaskQueue
from modules.storage_module.file_storage import FileStorage
from repositories.submission_state_repo import SubmissionStateRepository
from services.evaluation_service import EvaluationService
from services.submission_service import SubmissionService
from modules.receive_module.mail_receiver import MailReceiver, MailSettings

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
    submission_service: SubmissionService
    mail_receiver: MailReceiver

async def build_app_state() -> AppState:
    config = load_settings()
    logger = build_logger(config.log_dir)


    storage = FileStorage(config.code_storage_dir)

    b3 = B3Client(config.b3_base_url, timeout_s=config.http_timeout_s, retry_count=config.http_retry_count)
    b4 = B4Client(config.b4_base_url, timeout_s=config.http_timeout_s, retry_count=config.http_retry_count)
    repo = SubmissionStateRepository(b4=b4)

    evaluator = EvaluationService(repo=repo, b3=b3, b4=b4, logger=logger)
    queue = AsyncTaskQueue(worker_count=config.worker_count, handler=evaluator.handle_submission)

    submission_service = SubmissionService(
        config=config,
        repo=repo,
        storage=storage,
        queue=queue,
        logger=logger,
    )

    mail_settings = MailSettings(
        enabled=config.mail_enabled,
        imap_host=config.mail_imap_host,
        imap_port=config.mail_imap_port,
        username=config.mail_username,
        password=config.mail_password,
        poll_interval_s=config.mail_poll_interval_s,
    )
    mail_receiver = MailReceiver(
        settings=mail_settings,
        logger=logger,
        submission_service=submission_service
    )

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
        submission_service=submission_service,
        mail_receiver=mail_receiver,
    )


async def shutdown_app_state(state: AppState) -> None:
    try:
        await state.queue.stop()
        if hasattr(state.mail_receiver, 'stop'):
            await state.mail_receiver.stop()
    finally:
        await state.b3.close()
        await state.b4.close()
