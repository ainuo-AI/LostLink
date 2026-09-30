"""物品记录的数据访问模块。

生产实现把筛选、计数、排序和分页交给 MySQL；内存实现仅作为快速自动测试的替身。
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.item import Item
from app.schemas.item import Campus, CampusArea, ItemRead, ItemStatus, RecordType


@dataclass(frozen=True, slots=True)
class ItemFilters:
    """Repository 可以执行的数据库筛选与分页条件。"""

    keyword: str | None
    item_type: RecordType | None
    category: str | None
    campus: Campus | None
    area: CampusArea | None
    status: ItemStatus
    occurred_after: datetime | None
    offset: int
    limit: int


class ItemRepository(Protocol):
    """声明业务层需要的数据访问能力。"""

    def list_filtered(self, filters: ItemFilters) -> tuple[list[ItemRead], int]:
        """返回当前页记录和筛选后的总数。"""


class SqlAlchemyItemRepository:
    """使用 SQLAlchemy Session 查询 MySQL 的正式仓储实现。"""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_filtered(self, filters: ItemFilters) -> tuple[list[ItemRead], int]:
        """在数据库中完成组合筛选、稳定排序和分页。"""

        statement = self._apply_filters(select(Item), filters)

        # 计数语句复用相同 WHERE 条件，但不携带排序和分页，保证 total 准确。
        count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
        total = self.session.scalar(count_statement) or 0

        page_statement = (
            statement.order_by(Item.occurred_at.desc(), Item.id.desc())
            .offset(filters.offset)
            .limit(filters.limit)
        )
        rows = self.session.scalars(page_statement).all()
        return [self._to_schema(row) for row in rows], total

    @staticmethod
    def _apply_filters(statement: Select, filters: ItemFilters) -> Select:
        """把业务筛选条件转换为 SQLAlchemy WHERE 表达式。"""

        statement = statement.where(Item.status == filters.status.value)

        if filters.keyword and (keyword := filters.keyword.strip()):
            # 转义 LIKE 通配符，确保用户输入的 % 和 _ 被当作普通字符搜索。
            escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            statement = statement.where(
                or_(
                    Item.title.like(pattern, escape="\\"),
                    Item.description.like(pattern, escape="\\"),
                    Item.location.like(pattern, escape="\\"),
                    Item.category.like(pattern, escape="\\"),
                    Item.campus.like(pattern, escape="\\"),
                    Item.area.like(pattern, escape="\\"),
                )
            )
        if filters.item_type:
            statement = statement.where(Item.type == filters.item_type.value)
        if filters.category:
            statement = statement.where(Item.category == filters.category.strip())
        if filters.campus:
            statement = statement.where(Item.campus == filters.campus.value)
        if filters.area:
            statement = statement.where(Item.area == filters.area.value)
        if filters.occurred_after:
            # 写入 MySQL 前移除 tzinfo，数据库中的 DATETIME 始终按 UTC 解释。
            utc_naive = filters.occurred_after.astimezone(UTC).replace(tzinfo=None)
            statement = statement.where(Item.occurred_at >= utc_naive)

        return statement

    @staticmethod
    def _to_schema(item: Item) -> ItemRead:
        """把数据库模型转换为稳定的公开响应结构。"""

        occurred_at = item.occurred_at
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)
        else:
            occurred_at = occurred_at.astimezone(UTC)

        return ItemRead(
            id=item.id,
            type=item.type,
            category=item.category,
            title=item.title,
            description=item.description,
            location=item.location,
            campus=item.campus,
            area=item.area,
            occurred_at=occurred_at,
            status=item.status,
            contact_hint=item.contact_hint,
        )


class InMemoryItemRepository:
    """不连接数据库的测试仓储，行为与正式仓储保持一致。"""

    def __init__(self, items: list[ItemRead] | None = None) -> None:
        self._items = list(items or [])

    def list_filtered(self, filters: ItemFilters) -> tuple[list[ItemRead], int]:
        """在内存中执行等价筛选，供接口单元测试快速运行。"""

        items = [item for item in self._items if item.status == filters.status]

        if filters.keyword and (keyword := filters.keyword.strip().casefold()):
            items = [item for item in items if self._matches_keyword(item, keyword)]
        if filters.item_type:
            items = [item for item in items if item.type == filters.item_type]
        if filters.category:
            category = filters.category.strip().casefold()
            items = [item for item in items if item.category.casefold() == category]
        if filters.campus:
            items = [item for item in items if item.campus == filters.campus]
        if filters.area:
            items = [item for item in items if item.area == filters.area]
        if filters.occurred_after:
            items = [item for item in items if item.occurred_at >= filters.occurred_after]

        items.sort(key=lambda item: (item.occurred_at, item.id), reverse=True)
        total = len(items)
        return items[filters.offset : filters.offset + filters.limit], total

    @staticmethod
    def _matches_keyword(item: ItemRead, keyword: str) -> bool:
        """在与 MySQL 查询相同的公开文本字段中执行包含搜索。"""

        searchable_fields = (
            item.title,
            item.description,
            item.location,
            item.category,
            item.campus.value,
            item.area.value if item.area else "",
        )
        return any(keyword in field.casefold() for field in searchable_fields)
