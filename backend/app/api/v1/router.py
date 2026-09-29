"""v1 路由汇总模块。"""

from fastapi import APIRouter

from app.api.v1.items import router as items_router

router = APIRouter()
router.include_router(items_router)
