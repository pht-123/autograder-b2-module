# Task: Static Check Rule Design

## Goal
Define how B2 consumes B3-provided rules (`forbidden_modules`, `forbidden_functions`) and turns them into AST scan rules.

## Where It's Implemented
- Rule source: [B3Client.get_question_rules](file:///Users/bytedance/Desktop/作业/b2_project/app/clients/b3_client.py)
- Rule application: [ForbiddenChecker.check](file:///Users/bytedance/Desktop/作业/b2_project/app/modules/static_check_module/checkers.py)

