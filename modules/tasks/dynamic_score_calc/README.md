# Task: Dynamic Evaluation Score Calculation

## Goal
Ensure B2 always returns a meaningful `overall_score`.

## Policy
- Prefer B3-provided `overall_score`.
- If absent but `passed_count/total_count` are present, compute:
  - `overall_score = passed_count / total_count * 100`

## Implementation
- [EvaluationService._merge_dynamic](file:///Users/bytedance/Desktop/作业/b2_project/app/services/evaluation_service.py)

