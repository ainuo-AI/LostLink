"""物品列表查询业务逻辑。

Service 负责默认状态和分页边界，再委托 Repository 在数据源中执行查询。
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.repositories.item_repository import ItemFilters, ItemRepository
from app.schemas.item import (
    Campus,
    CampusArea,
    ItemListResponse,
    ItemStatus,
    RecordType,
)


@dataclass(frozen=True, slots=True)
class ItemQuery:
    """Service 使用的纯 Python 查询条件。"""

    keyword: str | None = None
    item_type: RecordType | None = None
    category: str | None = None
    campus: Campus | None = None
    area: CampusArea | None = None
    status: ItemStatus | None = None
    days: int | None = None
    page: int = 1
    page_size: int = 20


class ItemService:
    """编排记录查询规则。"""

    def __init__(self, repository: ItemRepository) -> None:
        self.repository = repository

    def list_items(
        self,
        query: ItemQuery,
        *,
        now: datetime | None = None,
    ) -> ItemListResponse:
        """筛选、排序并分页返回公开记录。"""

        current_time = now or datetime.now(UTC)
        # 没有显式指定状态时只展示进行中的记录，防止失效信息重新出现在首页。
        filters = ItemFilters(
            keyword=query.keyword,
            item_type=query.item_type,
            category=query.category,
            campus=query.campus,
            area=query.area,
            status=query.status or ItemStatus.ACTIVE,
            occurred_after=current_time - timedelta(days=query.days) if query.days else None,
            offset=(query.page - 1) * query.page_size,
            limit=query.page_size,
        )
        items, total = self.repository.list_filtered(filters)

        return ItemListResponse(
            items=items,
            page=query.page,
            page_size=query.page_size,
            total=total,
        )
