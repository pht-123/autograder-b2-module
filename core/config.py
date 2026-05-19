from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass()
class Settings:
    project_root: Path
    code_storage_dir: Path
    log_dir: Path
    b3_base_url: str
    b4_base_url: str
    worker_count: int
    http_timeout_s: float
    http_retry_count: int


def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[2]

    ##代码和日志存储位置，需要配置环境变量，否则默认根目录下code和log文件夹，根据设计进行沟通！！！
    code_storage_dir = Path(os.getenv("CODE_STORAGE_DIR", project_root / "code"))
    log_dir = Path(os.getenv("LOG_DIR", project_root / "logs"))

    return Settings(
        project_root=project_root,
        code_storage_dir=code_storage_dir,
        log_dir=log_dir,
        b3_base_url=os.getenv("B3_BASE_URL", "http://localhost:8003"),
        b4_base_url=os.getenv("B4_BASE_URL", "http://localhost:8000"),
        worker_count=int(os.getenv("WORKER_COUNT", "2")),
        http_timeout_s=float(os.getenv("HTTP_TIMEOUT_S", "10")),
        http_retry_count=int(os.getenv("HTTP_RETRY_COUNT", "3")),
    )

