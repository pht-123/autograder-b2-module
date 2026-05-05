# Task: Sandbox Environment Setup

## Goal
Clarify the B2-side responsibility for sandboxing.

## Boundary
- Actual sandbox execution belongs to B3.
- B2 only forwards:
  - `submission_id`
  - `question_id`
  - `submitted_code`
  - `language`

## Integration Point
- [B3Client.evaluate](file:///Users/bytedance/Desktop/作业/b2_project/app/clients/b3_client.py)

