from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.modules.exception_module.errors import IntegrationError


class BaseHttpClient:
    def __init__(self, base_url: str, timeout_s: float, retry_count: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.retry_count = retry_count
        self.client = httpx.AsyncClient(timeout=timeout_s)

    async def close(self) -> None:
        await self.client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(1, self.retry_count + 1):
            try:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise IntegrationError(f"unexpected payload from {url}")
                return payload
            except Exception as exc:  # pragma: no cover - defensive integration wrapper
                last_error = exc
                if attempt < self.retry_count:
                    await asyncio.sleep(0.25 * attempt)
        raise IntegrationError(f"{method} {url} failed: {last_error}") from last_error

