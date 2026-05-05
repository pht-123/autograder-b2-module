# Task: Performance Optimization

## Goal
Keep submission API fast and avoid blocking evaluation on HTTP thread.

## Applied Design
- Async evaluation uses an in-process queue.
- HTTP calls to B3/B4 use timeouts and retries.
- File IO is limited to a single write on submit and a single read on evaluation.

Relevant code:
- [AsyncTaskQueue](file:///Users/bytedance/Desktop/作业/b2_project/app/core/task_queue.py)
- [BaseHttpClient](file:///Users/bytedance/Desktop/作业/b2_project/app/clients/base.py)

