"""失物与拾物记录查询接口。

API 层只负责接收和校验 HTTP 参数，再把查询工作交给 Service；它不直接读取数据源。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_item_repository
from app.repositories.item_repository import ItemRepository
from app.schemas.item import (
    Campus,
    CampusArea,
    ItemListResponse,
    ItemStatus,
    RecordType,
)
from app.services.item_service import ItemQuery, ItemService

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=ItemListResponse, summary="查询失物与拾物记录")
def list_items(
    repository: Annotated[ItemRepository, Depends(get_item_repository)],
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
    service = ItemService(repository)
    return service.list_items(query)
