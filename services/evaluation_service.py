from __future__ import annotations

import logging
from pathlib import Path

from clients.b3_client import B3Client
from clients.b4_client import B4Client
from models.submission import CaseResult, SubmissionState
from modules.exception_module.errors import EvaluationError
from modules.static_check_module.checkers import ForbiddenChecker, SyntaxChecker
from repositories.submission_state_repo import SubmissionStateRepository


class EvaluationService:
    def __init__(
        self,
        repo: SubmissionStateRepository,
        b3: B3Client,
        b4: B4Client,
        logger: logging.Logger,
    ) -> None:
        self._repo = repo
        self._b3 = b3
        self._b4 = b4
        self._logger = logger
        self._syntax = SyntaxChecker()
        self._forbidden = ForbiddenChecker()

    async def handle_submission(self, submission_id: str) -> None:
        state = await self._repo.get(submission_id)
        state.status = "RUNNING"
        await self._repo.save(state)

        self._logger.info("event=evaluation_start submission_id=%s", submission_id)

        try:
            await self._evaluate(state)
        except Exception as exc:
            state.status = "ERROR"
            state.overall_score = 0.0
            state.overall_comment = f"评测失败: {exc}"
            await self._repo.save(state)
            self._logger.exception("event=evaluation_error submission_id=%s", submission_id)
            raise EvaluationError(str(exc)) from exc

        self._logger.info("event=evaluation_done submission_id=%s status=%s", submission_id, state.status)

    async def _evaluate(self, state: SubmissionState) -> None:
        # 1) Get static rules from B3
        rules = await self._b3.get_question_rules(state.question_id)
        forbidden_modules = list(rules.get("forbidden_modules") or [])
        forbidden_functions = list(rules.get("forbidden_functions") or [])

        # 2) Static check (syntax + forbidden)
        code = self._load_code(state)

        syntax_issues = self._syntax.check(code, language=state.language)
        forbidden_issues = self._forbidden.check(code, forbidden_modules, forbidden_functions, language=state.language)

        state.static_issues = [*syntax_issues, *forbidden_issues]

        if syntax_issues:
            state.status = "ERROR"
            state.overall_score = 0.0
            state.overall_comment = "语法错误，无法运行动态测评"
            await self._repo.save(state)
            await self._sync_b4_best_effort(state)
            return

        eval_result = await self._b3.evaluate(
            submission_id=state.submission_id,
            question_id=state.question_id,
            submitted_code=state.submitted_code,
            language=state.language,
        )

        self._merge_dynamic(state, eval_result)

        # 4) Merge comment with static info (keep score policy simple per docs)
        if state.static_issues:
            state.overall_comment = (state.overall_comment or "").strip()
            suffix = f"（静态检查发现 {len(state.static_issues)} 项问题）"
            state.overall_comment = f"{state.overall_comment}{suffix}" if state.overall_comment else suffix

        state.status = "COMPLETED"
        await self._repo.save(state)

        # 5) Sync to B4
        await self._sync_b4_best_effort(state)

    def _load_code(self, state: SubmissionState) -> str:
        if not state.code_path:
            raise EvaluationError("missing code_path in submission state")
        path = Path(state.code_path)
        try:
            return path.read_text(encoding="utf-8")
        except Exception as exc:
            raise EvaluationError(f"failed to read code file: {path}") from exc

    @staticmethod
    def _merge_dynamic(state: SubmissionState, dynamic: dict) -> None:
        passed = int(dynamic.get("passed_count") or 0)
        total = int(dynamic.get("total_count") or 0)
        score = dynamic.get("overall_score")
        if score is None and total > 0:
            # Fallback score policy when B3 does not return a score.
            score = (passed / total) * 100.0

        state.overall_score = float(score or 0.0)
        state.passed_count = passed
        state.total_count = total
        state.overall_comment = str(dynamic.get("overall_comment") or "")
        state.case_results = [CaseResult.model_validate(x) for x in (dynamic.get("case_results") or [])]

    async def _sync_b4_best_effort(self, state: SubmissionState) -> None:
        payload = {
            "status": state.status,
            "overallScore": state.overall_score,
            "passedCount": state.passed_count,
            "totalCount": state.total_count,
            "overallComment": state.overall_comment,
            "staticIssues": [x.model_dump() for x in state.static_issues],
            "caseResults": [x.model_dump() for x in state.case_results],
        }
        try:
            await self._b4.sync_result(state.submission_id, payload)
        except Exception:
            # B4 integration may not be available in the homework environment.
            self._logger.exception("event=b4_sync_failed submission_id=%s", state.submission_id)
