from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = Field(default=200)
    message: str = Field(default="success")
    data: T

    @classmethod
    def ok(cls, data: T) -> "ApiResponse[T]":
        return cls(data=data)


class ErrorPayload(BaseModel):
    code: int
    message: str
