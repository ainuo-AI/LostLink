"""v1 路由汇总模块。"""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.items import router as items_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.reports import router as reports_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.users import router as users_router

router = APIRouter()
# v1 总路由只负责聚合资源模块；每个子模块维护自己的前缀和标签。
router.include_router(auth_router)
router.include_router(items_router)
router.include_router(users_router)
router.include_router(uploads_router)
router.include_router(reports_router)
router.include_router(notifications_router)
router.include_router(admin_router)
