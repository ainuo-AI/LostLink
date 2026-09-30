"""API 总路由。

所有版本化接口先在这里汇总，使未来增加 v2 时不会影响应用入口。
"""

from fastapi import APIRouter

from app.api.v1.router import router as v1_router

api_router = APIRouter()
api_router.include_router(v1_router)
