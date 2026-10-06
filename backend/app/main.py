"""FastAPI 应用入口。

这个模块只负责组装配置、中间件、异常处理器和路由，业务逻辑放在 Service 中，
避免应用入口随着功能增加而变得难以维护。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.middleware import RequestIdMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """创建一个可独立配置的 FastAPI 实例，方便正式运行和自动测试复用。"""

    current_settings = settings or get_settings()
    application = FastAPI(
        title=current_settings.app_name,
        version=current_settings.app_version,
        description="校园失物招领信息查询与管理 API",
    )
    # 路由依赖读取与本应用实例相同的配置，避免测试或多实例运行时混用全局配置。
    application.dependency_overrides[get_settings] = lambda: current_settings

    # 请求标识中间件为每次请求生成唯一编号，方便把接口错误与服务端日志关联起来。
    application.add_middleware(RequestIdMiddleware)

    # CORS 仅放行配置中的前端地址，避免浏览器默认阻止本地前后端联调。
    application.add_middleware(
        CORSMiddleware,
        allow_origins=current_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 统一注册错误处理器和版本化路由，使所有接口遵守相同的响应规则。
    register_exception_handlers(application)
    application.include_router(api_router, prefix=current_settings.api_v1_prefix)

    @application.get("/health", tags=["system"], summary="检查服务状态")
    async def health_check() -> dict[str, str]:
        """返回轻量健康信息；后续接入数据库时可扩展依赖状态检查。"""

        return {
            "status": "ok",
            "service": current_settings.app_name,
            "version": current_settings.app_version,
            "environment": current_settings.app_env,
        }

    return application


# Uvicorn 默认加载这个实例；测试则调用 create_app 创建隔离的应用。
app = create_app()
