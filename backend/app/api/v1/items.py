"""失物与拾物记录查询和管理接口。

API 层只负责接收参数、注入当前用户并选择 HTTP 状态码；公开查询、资源归属、
跨字段规则和状态转换统一交给 ItemService。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_current_user, get_item_service
from app.schemas.auth import UserRead
from app.schemas.item import (
    Campus,
    CampusArea,
    ItemCreate,
    ItemListResponse,
    ItemOwnerRead,
    ItemRead,
    ItemStatus,
    ItemStatusUpdate,
    ItemUpdate,
    RecordType,
)
from app.services.item_service import ItemQuery, ItemService

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=ItemListResponse, summary="查询失物与拾物记录")
def list_items(
    service: Annotated[ItemService, Depends(get_item_service)],
    keyword: Annotated[
        str | None,
        Query(max_length=100, description="同时搜索标题、描述、类别和地点"),
    ] = None,
    item_type: Annotated[
        RecordType | None,
        Query(alias="type", description="记录类型：lost 或 found"),
    ] = None,
    category: Annotated[str | None, Query(max_length=50)] = None,
    campus: Campus | None = None,
    area: CampusArea | None = None,
    status: ItemStatus | None = None,
    days: Annotated[int | None, Query(ge=1, le=365)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ItemListResponse:
    """根据筛选条件返回稳定排序、带分页信息的公开记录。

    这里使用同步函数，让 FastAPI 在线程池中执行同步 SQLAlchemy 查询，避免阻塞事件循环。
    """

    # 将 HTTP 参数转换为内部查询对象，避免 Service 依赖 FastAPI 的 Query 类型。
    query = ItemQuery(
        keyword=keyword,
        item_type=item_type,
        category=category,
        campus=campus,
        area=area,
        status=status,
        days=days,
        page=page,
        page_size=page_size,
    )
    return service.list_items(query)


@router.get("/{item_id}", response_model=ItemRead, summary="读取公开物品详情")
def get_item(
    item_id: int,
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemRead:
    """返回指定记录的公开字段和联系方式，不暴露发布者管理字段。"""

    return service.get_public_item(item_id)


@router.post(
    "",
    response_model=ItemOwnerRead,
    status_code=status.HTTP_201_CREATED,
    summary="发布失物或拾物记录",
)
def create_item(
    payload: ItemCreate,
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemOwnerRead:
    """发布记录并由服务端把所有者固定为当前登录用户。"""

    return service.create_item(payload, user)


@router.patch("/{item_id}", response_model=ItemOwnerRead, summary="编辑自己的物品记录")
def update_item(
    item_id: int,
    payload: ItemUpdate,
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemOwnerRead:
    """只允许发布者或管理员修改 active 记录的白名单字段。"""

    return service.update_item(item_id, payload, user)


@router.patch(
    "/{item_id}/status",
    response_model=ItemOwnerRead,
    summary="完成或关闭自己的物品记录",
)
def update_item_status(
    item_id: int,
    payload: ItemStatusUpdate,
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemOwnerRead:
    """执行类型匹配的终态转换，并写入状态变化审计。"""

    return service.update_status(item_id, payload, user)
