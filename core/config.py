from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    project_root: Path
    code_storage_dir: Path
    log_dir: Path
    b3_base_url: str
    b4_base_url: str
    worker_count: int
    http_timeout_s: float
    http_retry_count: int

    mail_enabled: bool = False
    mail_imap_host: str = "imap.qq.com"
    mail_imap_port: int = 993
    mail_username: str = ""       # QQ邮箱地址
    mail_password: str = ""       # QQ邮箱授权码（非登录密码）
    mail_poll_interval_s: int = 10


def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[2]
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

        mail_enabled=os.getenv("MAIL_ENABLED", "false").lower() == "true",
        mail_imap_host=os.getenv("MAIL_IMAP_HOST", "imap.qq.com"),
        mail_imap_port=int(os.getenv("MAIL_IMAP_PORT", "993")),
        mail_username=os.getenv("MAIL_USERNAME", ""),
        mail_password=os.getenv("MAIL_PASSWORD", ""),
        mail_poll_interval_s=int(os.getenv("MAIL_POLL_INTERVAL_S", "10")),
    )

