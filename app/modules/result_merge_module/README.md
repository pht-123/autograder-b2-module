# ResultMergeModule

## Purpose
Combine:
- static check results (syntax + forbidden scan)
- dynamic evaluation results from B3
into a single submission report and a payload for B4 writeback.

## Implementation
The merge happens inside:
- [EvaluationService](file:///Users/bytedance/Desktop/作业/b2_project/app/services/evaluation_service.py)

Scoring policy (homework default):
- Prefer B3-provided `overall_score`
- Append static issue info into `overall_comment`

