from __future__ import annotations

from fastapi import APIRouter, Request

from app.models.common import ApiResponse
from app.models.submission import SubmissionCreateRequest, SubmissionCreateResponse, SubmissionState
from app.services.submission_service import SubmissionService

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

