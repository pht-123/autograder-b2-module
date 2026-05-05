# StorageModule

## Purpose
Persist the submitted source code to the local filesystem.

## Constraints
- B2 must not own business tables and must not connect to DB.
- Code is the only persistent data B2 stores.

## Storage Layout
`code/{assignment_id}/{question_id}/{student_user_id}/{submission_id}.py`

## Implementation
- [file_storage.py](file:///Users/bytedance/Desktop/作业/b2_project/app/modules/storage_module/file_storage.py)

