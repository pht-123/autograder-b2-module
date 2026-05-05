# SyncModule

## Purpose
Write back merged evaluation results to B4:
`PATCH /api/v1/submissions/{submission_id}/result`

## Implementation
Best-effort writeback is done inside:
- [EvaluationService._sync_b4_best_effort](file:///Users/bytedance/Desktop/作业/b2_project/app/services/evaluation_service.py)

