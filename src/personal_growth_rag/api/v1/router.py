"""API v1 总路由与统一错误出口。

成功和失败都返回同一层 envelope，前端可以稳定读取 success/error_code/message/data。
"""

import logging

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from personal_growth_rag.api.v1.contracts.common import error
from personal_growth_rag.api.v1.routes.documents import router as documents_router
from personal_growth_rag.api.v1.routes.health import router as health_router
from personal_growth_rag.api.v1.routes.questions import router as questions_router
from personal_growth_rag.api.v1.routes.search import router as search_router
from personal_growth_rag.core.errors import AppError

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/v1")
api_router.include_router(health_router)
api_router.include_router(documents_router)
api_router.include_router(search_router)
api_router.include_router(questions_router)


def register_exception_handlers(app: FastAPI) -> None:
    # route/application 抛 AppError；这里是唯一的 HTTP 错误格式转换点。
    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code.value >= 500:
            logger.error("Application error: %s", exc)
        return JSONResponse(
            status_code=exc.status_code.value,
            content=error(exc.error_code, exc.message).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        error_code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        message = "Not found" if exc.status_code == 404 else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=error(error_code, message).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        message = _format_validation_message(exc)
        return JSONResponse(
            status_code=422,
            content=error("VALIDATION_ERROR", message).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unexpected error: %s", exc)
        return JSONResponse(
            status_code=500,
            content=error("INTERNAL_ERROR", "Internal error").model_dump(),
        )


def _format_validation_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "Invalid request"

    first_error = errors[0]
    loc = ".".join(str(item) for item in first_error.get("loc", []))
    message = str(first_error.get("msg", "Invalid request"))
    return f"{loc}: {message}" if loc else message
