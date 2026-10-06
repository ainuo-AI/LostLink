"""认证模块的 HTTP API 边界。

路由只负责接收经过 Schema 校验的请求、注入 ``AuthService`` 并选择 HTTP
状态码；密码处理、会话策略和数据库事务全部下沉到 Service 与 Repository。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_auth_service, get_bearer_token
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="注册校园账号",
)
def register(
    payload: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserRead:
    """创建普通用户；校园身份默认保持未验证。"""

    return service.register(payload)


@router.post("/login", response_model=TokenResponse, summary="登录并创建会话")
def login(
    payload: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """验证账号密码并返回一次性可见的 Bearer 令牌。"""

    return service.login(payload)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="退出并吊销当前会话",
)
def logout(
    token: Annotated[str, Depends(get_bearer_token)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    """仅吊销发起请求的当前会话。"""

    service.logout(token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
