from __future__ import annotations

from typing import Any

from clients.base import BaseHttpClient


class B3Client(BaseHttpClient):
    async def get_question_rules(self, question_id: str) -> dict[str, Any]:
        payload = await self._request("GET", f"/api/v1/b3/questions/{question_id}")
        return payload.get("data", {})

    async def evaluate(
        self,
        submission_id: str,
        question_id: str,
        submitted_code: str,
        language: str,
    ) -> dict[str, Any]:
        payload = await self._request(
            "POST",
            "/api/v1/b3/evaluate",
            json={
                "submission_id": submission_id,
                "question_id": question_id,
                "submitted_code": submitted_code,
                "language": language,
            },
        )
        return payload.get("data", {})

