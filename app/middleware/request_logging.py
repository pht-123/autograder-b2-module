from __future__ import annotations

import time
from typing import Callable

from fastapi import FastAPI, Request, Response


def install_request_logging(app: FastAPI) -> None:
    @app.middleware("http")
    async def _log_requests(request: Request, call_next: Callable[[Request], Response]) -> Response:
        start = time.time()
        response = await call_next(request)
        elapsed_ms = (time.time() - start) * 1000.0

        b2 = getattr(request.app.state, "b2", None)
        logger = getattr(b2, "logger", None)
        if logger is not None:
            logger.info(
                "event=request method=%s path=%s status=%s latency_ms=%.2f",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )
        return response

