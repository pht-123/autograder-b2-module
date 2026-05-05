# ReceiveModule

## Purpose
Handle incoming submissions via:
- HTTP API (B1 -> B2)
- Mail receiver (IMAP poll + SMTP receipt) skeleton

## HTTP Flow (Implemented)
- Validate request
- Generate `submission_id`
- Persist code to filesystem
- Enqueue async evaluation

Code entry:
- API router: [submissions.py](file:///Users/bytedance/Desktop/作业/b2_project/app/api/v1/submissions.py)
- Service: [SubmissionService](file:///Users/bytedance/Desktop/作业/b2_project/app/services/submission_service.py)

## Mail Flow (Skeleton)
Mail receiver is a configurable background loop:
- Poll IMAP inbox
- Parse body/attachments into a submission request
- Map `student_id` -> `student_user_id` via B4
- Send SMTP receipt (success/failure)

Skeleton code:
- [mail_receiver.py](file:///Users/bytedance/Desktop/作业/b2_project/app/modules/receive_module/mail_receiver.py)

