# Task: Logic Self-Test / Bug Fix

## Goal
Keep the code path consistent and avoid common integration failures.

## Checklist (Applied)
- Always persist code to filesystem before enqueue.
- Always update submission state (`PENDING` -> `RUNNING` -> `COMPLETED/ERROR`).
- Best-effort B4 sync; do not crash the API server if B4 is unavailable.
- Fallback score policy when B3 omits `overall_score`.

Key code:
- [SubmissionService](file:///Users/bytedance/Desktop/作业/b2_project/app/services/submission_service.py)
- [EvaluationService](file:///Users/bytedance/Desktop/作业/b2_project/app/services/evaluation_service.py)

