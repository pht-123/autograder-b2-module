from __future__ import annotations

from typing import Any

from app.clients.base import BaseHttpClient


class B4Client(BaseHttpClient):
    async def map_student(self, student_id: str) -> dict[str, Any]:
        payload = await self._request("GET", "/api/v1/students/mapping", params={"student_id": student_id})
        return payload.get("data", {})

    async def sync_result(self, submission_id: str, result_payload: dict[str, Any]) -> None:
        await self._request("PATCH", f"/api/v1/submissions/{submission_id}/result", json=result_payload)

