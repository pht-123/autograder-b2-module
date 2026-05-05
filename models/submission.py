from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SubmissionStatus = Literal["PENDING", "RUNNING", "COMPLETED", "ERROR"]


class SubmissionCreateRequest(BaseModel):
    student_user_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    assignment_id: str = Field(min_length=1)
    code: str = Field(min_length=1)
    language: str = Field(default="python")


class SubmissionCreateResponse(BaseModel):
    submission_id: str
    status: SubmissionStatus


class StaticIssue(BaseModel):
    type: str
    message: str
    line: int | None = None


class CaseResult(BaseModel):
    case_id: str
    passed: bool
    expected_output: str = ""
    actual_output: str = ""
    execution_time_ms: float = 0.0
    error: str | None = None


class SubmissionState(BaseModel):
    submission_id: str
    student_user_id: str
    question_id: str
    assignment_id: str
    # Internal-only field for reading the persisted code back during evaluation.
    code_path: str | None = Field(default=None, exclude=True)
    status: SubmissionStatus
    overall_score: float | None = None
    passed_count: int | None = None
    total_count: int | None = None
    overall_comment: str | None = None
    static_issues: list[StaticIssue] = Field(default_factory=list)
    case_results: list[CaseResult] = Field(default_factory=list)
