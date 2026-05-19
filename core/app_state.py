from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial

from api_and_client.api_and_client import call_b3_evaluate, write_result_to_b4
from core.config import Settings, load_settings
from core.logging import build_logger
from core.task_queue import AsyncTaskQueue
from modules.storage_module.file_storage import FileStorage
from repositories.submission_state_repo import SubmissionStateRepository
from services.evaluation_service import EvaluationService


@dataclass(slots=True)
class AppState:
    config: Settings
    logger: logging.Logger
    repo: SubmissionStateRepository
    storage: FileStorage
    b3: call_b3_evaluate
    b4: write_result_to_b4
    queue: AsyncTaskQueue
    evaluator: EvaluationService


async def build_app_state() -> AppState:
    config = load_settings()   ##装载配置
    logger = build_logger(config.log_dir)    ##创建日志工具

    repo = SubmissionStateRepository()
    storage = FileStorage(config.code_storage_dir)

    # 绑定 B3/B4 的基础配置（base_url、超时、重试），返回可直接调用的函数
    b3 = partial(
        call_b3_evaluate,
        base_url=config.b3_base_url,
        timeout_s=config.http_timeout_s,
        retry_count=config.http_retry_count
    )
    b4 = partial(
        write_result_to_b4,
        base_url=config.b4_base_url,
        timeout_s=config.http_timeout_s,
        retry_count=config.http_retry_count
    )

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
        # 修正：call_b3_evaluate/write_result_to_b4 是函数，无 close 方法，需移除
        # await state.b3.close()
        # await state.b4.close()
        pass  # 若 httpx.Client 有连接池，需在 api_and_client.py 中统一管理关闭