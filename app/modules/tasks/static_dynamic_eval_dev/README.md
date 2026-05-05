# Task: Static / Dynamic Evaluation Development

## Goal
Implement B2's end-to-end evaluation pipeline:
- static checks (local, no execution)
- dynamic checks (call B3 evaluate)
- merge and write back to B4

## Where It's Implemented
- Static checks: [checkers.py](file:///Users/bytedance/Desktop/作业/b2_project/app/modules/static_check_module/checkers.py)
- Dynamic evaluation + merge + B4 sync: [EvaluationService](file:///Users/bytedance/Desktop/作业/b2_project/app/services/evaluation_service.py)
- Async queue: [task_queue.py](file:///Users/bytedance/Desktop/作业/b2_project/app/core/task_queue.py)

