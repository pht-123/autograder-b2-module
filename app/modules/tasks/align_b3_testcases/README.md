# Task: Align With B3 Test Cases

## Goal
Ensure B2's request/response contract matches B3's evaluate API:
- request: `submission_id`, `question_id`, `submitted_code`, `language`
- response: `overall_score`, `passed_count`, `total_count`, `overall_comment`, `case_results[]`

## Implementation
- Request building: [B3Client.evaluate](file:///Users/bytedance/Desktop/作业/b2_project/app/clients/b3_client.py)
- Response mapping: [EvaluationService._merge_dynamic](file:///Users/bytedance/Desktop/作业/b2_project/app/services/evaluation_service.py)

