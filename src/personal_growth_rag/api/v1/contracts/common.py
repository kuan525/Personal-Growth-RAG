"""HTTP API 通用响应契约。"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    error_code: str | None = None
    message: str
    data: T | None = None
    request_id: str | None = None


class HealthData(BaseModel):
    status: str


def ok(data: T, message: str = "ok") -> ApiResponse[T]:
    return ApiResponse(success=True, error_code=None, message=message, data=data, request_id=None)


def error(error_code: str, message: str) -> ApiResponse[None]:
    return ApiResponse(
        success=False,
        error_code=error_code,
        message=message,
        data=None,
        request_id=None,
    )
