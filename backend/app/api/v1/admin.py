"""管理端概览、用户、审计和匹配校准接口。

本模块全部路由都依赖管理员守卫；具体状态规则与审计写入由 AdminService 负责。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_admin_service, require_admin
from app.schemas.auth import UserRead, UserStatus
from app.schemas.feature import (
    AdminUserListResponse,
    AuditLogListResponse,
    CalibrationTaskCreate,
    CalibrationTaskRead,
    CalibrationVersionAction,
    CalibrationVersionRead,
    OverviewRead,
    UserStatusUpdate,
)
from app.services.feature_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=OverviewRead)
def overview(
    _admin: Annotated[UserRead, Depends(require_admin)],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> OverviewRead:
    """返回管理台首页的核心计数。"""

    return service.overview()


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    _admin: Annotated[UserRead, Depends(require_admin)],
    service: Annotated[AdminService, Depends(get_admin_service)],
    keyword: Annotated[str | None, Query(max_length=100)] = None,
    user_status: Annotated[UserStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AdminUserListResponse:
    """筛选并分页查看用户账号。"""

    return service.list_users(keyword, user_status, page, page_size)


@router.patch("/users/{user_id}/status", response_model=UserRead)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    admin: Annotated[UserRead, Depends(require_admin)],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> UserRead:
    """限制或恢复普通用户，并留下操作理由。"""

    return service.update_user_status(user_id, payload, admin)


@router.get("/audit", response_model=AuditLogListResponse)
def list_audit_logs(
    _admin: Annotated[UserRead, Depends(require_admin)],
    service: Annotated[AdminService, Depends(get_admin_service)],
    action: Annotated[str | None, Query(max_length=64)] = None,
    object_type: Annotated[str | None, Query(max_length=32)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AuditLogListResponse:
    """按动作或对象类型查询管理员审计记录。"""

    return service.list_audits(action, object_type, page, page_size)


@router.post(
    "/calibration/tasks", response_model=CalibrationTaskRead, status_code=status.HTTP_201_CREATED
)
def create_calibration_task(
    payload: CalibrationTaskCreate,
    admin: Annotated[UserRead, Depends(require_admin)],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> CalibrationTaskRead:
    """创建一次同步校准评估并生成待审核候选版本。"""

    return service.create_calibration(payload, admin)


@router.get("/calibration/tasks", response_model=list[CalibrationTaskRead])
def list_calibration_tasks(
    _admin: Annotated[UserRead, Depends(require_admin)],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> list[CalibrationTaskRead]:
    """按时间倒序返回校准任务。"""

    return service.list_calibration_tasks()


@router.get("/calibration/versions", response_model=list[CalibrationVersionRead])
def list_calibration_versions(
    _admin: Annotated[UserRead, Depends(require_admin)],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> list[CalibrationVersionRead]:
    """按时间倒序返回所有权重版本。"""

    return service.list_calibration_versions()


@router.patch("/calibration/versions/{version_id}", response_model=CalibrationVersionRead)
def change_calibration_version(
    version_id: int,
    payload: CalibrationVersionAction,
    admin: Annotated[UserRead, Depends(require_admin)],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> CalibrationVersionRead:
    """审批、拒绝、启用或回滚一个权重版本。"""

    return service.change_calibration(version_id, payload, admin)
