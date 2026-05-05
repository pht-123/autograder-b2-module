from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from models.common import ApiResponse
from modules.exception_module.errors import (
    B2Error,
    EvaluationError,
    IntegrationError,
    NotFoundError,
    StorageError,
    ValidationError,
)


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def _validation(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content=ApiResponse(code=400, message=str(exc), data={}).model_dump())

    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content=ApiResponse(code=404, message=str(exc), data={}).model_dump())

    @app.exception_handler(StorageError)
    async def _storage(_: Request, exc: StorageError) -> JSONResponse:
        return JSONResponse(status_code=500, content=ApiResponse(code=500, message=str(exc), data={}).model_dump())

    @app.exception_handler(IntegrationError)
    async def _integration(_: Request, exc: IntegrationError) -> JSONResponse:
        return JSONResponse(status_code=502, content=ApiResponse(code=502, message=str(exc), data={}).model_dump())

    @app.exception_handler(EvaluationError)
    async def _evaluation(_: Request, exc: EvaluationError) -> JSONResponse:
        return JSONResponse(status_code=500, content=ApiResponse(code=500, message=str(exc), data={}).model_dump())

    @app.exception_handler(B2Error)
    async def _b2(_: Request, exc: B2Error) -> JSONResponse:
        return JSONResponse(status_code=500, content=ApiResponse(code=500, message=str(exc), data={}).model_dump())

