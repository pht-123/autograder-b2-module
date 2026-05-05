# ScheduleModule

## Purpose
Orchestrate dynamic evaluation by forwarding code to B3 `/evaluate`.

## Implementation
For this homework, scheduling is done by an in-process async task queue:
- Queue: [AsyncTaskQueue](file:///Users/bytedance/Desktop/作业/b2_project/app/core/task_queue.py)
- Handler: [EvaluationService.handle_submission](file:///Users/bytedance/Desktop/作业/b2_project/app/services/evaluation_service.py)

This is intentionally "lightweight" as required: Python asyncio + queue.

