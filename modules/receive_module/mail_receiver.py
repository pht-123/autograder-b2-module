from __future__ import annotations

"""
MailReceiver skeleton (IMAP polling + SMTP receipt).

This file is intentionally kept minimal for the homework deliverable:
- The business logic is defined by the docs, but real credentials and parsing rules
  depend on the deployment environment.
- The folder/module exists as a "deliverable module" from the weekly plan.
"""

import imaplib
import email
from email.header import decode_header
from typing import Any
from pathlib import Path
import asyncio
import logging
from dataclasses import dataclass
from services.submission_service import SubmissionService
from models.submission import SubmissionCreateRequest

@dataclass(slots=True)
class MailSettings:
    enabled: bool = False
    imap_host: str = "imap.qq.com"
    imap_port: int = 993
    username: str = ""
    password: str = ""
    poll_interval_s: int = 10


class MailReceiver:
    def __init__(
        self,
        settings: MailSettings,
        logger: logging.Logger,
        submission_service: SubmissionService,  # 方案 B：直接接收 Service
    ) -> None:
        self._settings = settings
        self._logger = logger
        self._submission_service = submission_service  # 保存 Service 引用

        self._stopping = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._imap: imaplib.IMAP4_SSL | None = None



    def _decode_str(self, s: str) -> str:
        """解码邮件头或附件名"""
        value, charset = decode_header(s)[0]
        if charset:
            try:
                value = value.decode(charset, errors='ignore')
            except Exception:
                value = value.decode('utf-8', errors='ignore')
        return value if isinstance(value, str) else str(value)

    def _extract_code_attachments(self, msg: email.message.EmailMessage) -> tuple[dict[str, str], str]:
        """提取附件中的代码文件，并推断主要语言"""
        code_files = {}
        primary_language = "unknown"

        # 语言推断映射表
        lang_map = {
            '.py': 'python', '.java': 'java', '.js': 'javascript',
            '.c': 'c', '.cpp': 'cpp', '.sh': 'shell', '.go': 'go',
        }

        for part in msg.walk():
            content_disposition = part.get_content_disposition()
            if content_disposition == 'attachment':
                filename = part.get_filename()
                if filename:
                    filename = self._decode_str(filename)
                    file_ext = Path(filename).suffix.lower()

                    if file_ext in lang_map:
                        # 优先解码为 utf-8，兼容 GBK
                        file_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        code_files[filename] = file_content
                        # 以第一个识别到的代码文件后缀作为主语言
                        if primary_language == "unknown":
                            primary_language = lang_map[file_ext]

        return code_files, primary_language


    async def _process_email(self, msg: email.message.EmailMessage) -> None:
        """解析单封邮件并推送到评测队列"""
        try:
            # 1. 提取发件人 (格式通常为 "昵称 <邮箱地址>")
            from_header = msg.get("From", "")
            sender_email = from_header.split("<")[-1].replace(">", "").strip()

            # 2. 提取正文 (备用，以防学生将代码贴在正文中)
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

            # 3. 提取附件代码及推断语言
            code_files, language = self._extract_code_attachments(msg)

            if not code_files and not body.strip():
                self._logger.warning(f"event=mail_no_code sender={sender_email}")
                return

            #4. 身份映射与提交流转
            # 4.1 将附件字典拼接为单份代码文本 (若多个文件，用分隔符隔开)
            submitted_code = "\n\n".join(
                f"# --- File: {fname} ---\n{content}"
                for fname, content in code_files.items()
            )
            if not submitted_code.strip() and body.strip():
                submitted_code = body  # 降级：若无附件代码则使用正文

            # 4.2 调用 SubmissionService 创建提交
            # 注意：这里假设 submission_service 提供了 create_submission 方法
            # question_id 暂时使用默认值或从邮件主题解析，这里以 "default_q" 为例
            payload = SubmissionCreateRequest(
                student_user_id=sender_email,  # 注意字段名对齐
                assignment_id="default_a",     # 补充必填项
                question_id="default_q",
                code=submitted_code,           # 注意字段名通常是 code 而非 submitted_code
                language=language,
            )
            await self._submission_service.create_submission(payload)

            self._logger.info(f"event=mail_parsed sender={sender_email} lang={language} files={list(code_files.keys())}")

        except Exception as e:
            self._logger.error(f"event=mail_parse_error error={e}")


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
            # 如果未启用或缺少凭证，则跳过连接
            if not self._settings.enabled or not self._settings.username:
                await asyncio.sleep(self._settings.poll_interval_s)
                continue

            try:
                #建立 IMAP 连接并登录
                self._imap = imaplib.IMAP4_SSL(
                    host=self._settings.imap_host,
                    port=self._settings.imap_port
                )
                self._imap.login(self._settings.username, self._settings.password)
                self._imap.select("INBOX")

                #搜索未读邮件
                status, message_ids = self._imap.search(None, "UNSEEN")
                if status == "OK" and message_ids[0]:
                    for msg_id in message_ids[0].split():
                        # 拉取邮件原始内容
                        status, msg_data = self._imap.fetch(msg_id, "(RFC822)")
                        if status == "OK":
                            raw_email = msg_data[0][1]
                            msg = email.message_from_bytes(raw_email)

                            # 开始解析
                            await self._process_email(msg)

                            #处理完毕，标记为已读
                            self._imap.store(msg_id, "+FLAGS", "\\Seen")

            except Exception as e:
                self._logger.error(f"event=mail_poll_error error={e}")
            finally:
                # 每次轮询结束登出，防止连接泄露被封禁
                if self._imap:
                    try:
                        self._imap.logout()
                    except Exception:
                        pass
                    self._imap = None

            #休眠等待下一轮
            await asyncio.sleep(self._settings.poll_interval_s)

        self._logger.info("event=mail_receiver_stop")

