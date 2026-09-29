"""统一异常与错误响应模块。

所有对外错误都使用 code、message、details 和 request_id，前端无需解析内部异常文本。
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class AppError(Exception):
    """表示可以安全返回给客户端的业务错误。"""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def _request_id(request: Request) -> str:
    """安全获取中间件生成的请求编号。"""

    return getattr(request.state, "request_id", "unknown")


def _error_content(
    request: Request,
    *,
    code: str,
    message: str,
    details: Any = None,
) -> dict[str, Any]:
    """构造项目统一的错误响应结构。"""

    return {
        "code": code,
        "message": message,
        "details": details,
        "request_id": _request_id(request),
    }


def register_exception_handlers(app: FastAPI) -> None:
    """给应用注册业务错误、参数错误和未知错误处理器。"""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_content(
                request,
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        # 只返回结构化校验信息，不暴露内部堆栈或请求中的敏感数据。
        details = [
            {
                "field": ".".join(str(part) for part in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_content(
                request,
                code="VALIDATION_ERROR",
                message="请求参数不正确",
                details=details,
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        # 数据库错误只记录异常类型和堆栈，不把连接地址或 SQL 参数返回给客户端。
        logger.exception("Database request failed", exc_info=exc)
        return JSONResponse(
            status_code=503,
            content=_error_content(
                request,
                code="DATABASE_UNAVAILABLE",
                message="数据服务暂时不可用，请稍后重试",
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # 未知异常写入服务端日志，但客户端只收到不含敏感信息的固定提示。
        logger.exception("Unhandled request error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=_error_content(
                request,
                code="INTERNAL_SERVER_ERROR",
                message="服务暂时不可用，请稍后重试",
            ),
        )
