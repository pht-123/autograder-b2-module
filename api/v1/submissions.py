from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from models.common import ApiResponse
from models.submission import SubmissionCreateRequest, SubmissionCreateResponse, SubmissionState
from services.submission_service import SubmissionService

router = APIRouter(tags=["submissions"])


@router.post("/submissions", response_model=ApiResponse[SubmissionCreateResponse])
async def create_submission(payload: SubmissionCreateRequest, request: Request) -> ApiResponse[SubmissionCreateResponse]:
    b2 = request.app.state.b2
    service = SubmissionService(
        config=b2.config,
        repo=b2.repo,
        storage=b2.storage,
        queue=b2.queue,
        logger=b2.logger,
    )
    result = await service.create_submission(payload)
    return ApiResponse.ok(result)


@router.get("/submissions/{submission_id}", response_model=ApiResponse[SubmissionState])
async def get_submission(submission_id: str, request: Request) -> ApiResponse[SubmissionState]:
    b2 = request.app.state.b2
    state = await b2.repo.get(submission_id)
    return ApiResponse.ok(state)


@router.get("/storage/codes", response_model=ApiResponse[list[dict]])
async def list_stored_codes(
    request: Request,
    assignment_id: Optional[str] = Query(None),
    question_id: Optional[str] = Query(None),
    student_user_id: Optional[str] = Query(None),
) -> ApiResponse[list[dict]]:
    """列出已持久化的待测代码文件"""
    b2 = request.app.state.b2
    results = list(b2.storage.list_codes(
        assignment_id=assignment_id,
        question_id=question_id,
        student_user_id=student_user_id,
    ))
    return ApiResponse.ok(results)


@router.get("/storage/codes/{submission_id}", response_class=PlainTextResponse)
async def read_stored_code(submission_id: str, request: Request) -> PlainTextResponse:
    """读取指定提交的源代码内容"""
    b2 = request.app.state.b2
    import glob as _glob
    matches = list(b2.storage.base_dir.rglob(f"{submission_id}.*"))
    if not matches:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="代码文件不存在")
    content = b2.storage.read_code(matches[0])
    return PlainTextResponse(content, media_type="text/plain; charset=utf-8")


@router.delete("/storage/codes/{submission_id}", response_model=ApiResponse)
async def delete_stored_code(submission_id: str, request: Request) -> ApiResponse:
    """删除指定的持久化代码文件"""
    b2 = request.app.state.b2
    import glob as _glob
    matches = list(b2.storage.base_dir.rglob(f"{submission_id}.*"))
    if not matches:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="代码文件不存在")
    b2.storage.delete_code(matches[0])
    return ApiResponse.ok(None)

