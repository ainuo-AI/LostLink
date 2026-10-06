"""用户举报提交、个人记录查询和管理员处理接口。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_current_user, get_report_service, require_admin
from app.schemas.auth import UserRead
from app.schemas.feature import (
    ReportCreate,
    ReportListResponse,
    ReportRead,
    ReportResolve,
    ReportStatus,
)
from app.services.feature_service import ReportService

router = APIRouter(tags=["reports"])


@router.post(
    "/items/{item_id}/reports", response_model=ReportRead, status_code=status.HTTP_201_CREATED
)
def create_report(
    item_id: int,
    payload: ReportCreate,
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[ReportService, Depends(get_report_service)],
) -> ReportRead:
    """举报一条不是自己发布的物品记录。"""

    return service.create(item_id, payload, user)


@router.get("/users/me/reports", response_model=ReportListResponse)
def list_my_reports(
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[ReportService, Depends(get_report_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ReportListResponse:
    """分页查看当前用户提交过的举报和处理结果。"""

    return service.list_mine(user, page, page_size)


@router.get("/admin/reports", response_model=ReportListResponse)
def list_admin_reports(
    _admin: Annotated[UserRead, Depends(require_admin)],
    service: Annotated[ReportService, Depends(get_report_service)],
    report_status: Annotated[ReportStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ReportListResponse:
    """管理员按处理状态筛选举报。"""

    return service.list_admin(report_status, page, page_size)


@router.patch("/admin/reports/{report_id}", response_model=ReportRead)
def resolve_report(
    report_id: int,
    payload: ReportResolve,
    admin: Annotated[UserRead, Depends(require_admin)],
    service: Annotated[ReportService, Depends(get_report_service)],
) -> ReportRead:
    """管理员对待处理举报作出一次性结论并记录审计。"""

    return service.resolve(report_id, payload, admin)
