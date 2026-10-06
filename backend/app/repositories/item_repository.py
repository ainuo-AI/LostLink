"""物品查询与管理的数据访问边界。

生产实现把筛选、计数、排序、写入和状态审计交给 MySQL；内存实现作为快速
自动测试替身。业务层只依赖本模块的 Protocol 和内部记录，不直接操作 ORM。
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.item_status_history import ItemStatusHistory
from app.schemas.item import (
    Campus,
    CampusArea,
    ItemOwnerRead,
    ItemRead,
    ItemStatus,
    RecordType,
    StorageMethod,
)


class ConcurrentItemUpdateError(Exception):
    """状态在读取和提交之间发生变化，需要客户端重新加载。"""


@dataclass(frozen=True, slots=True)
class ItemRecord:
    """Service 使用的完整内部记录，包含不对公众返回的管理字段。"""

    id: int
    owner_id: int | None
    type: RecordType
    category: str
    title: str
    description: str
    location: str
    campus: Campus
    area: CampusArea | None
    occurred_at: datetime
    status: ItemStatus
    contact_hint: str
    contact: str | None
    contact_note: str | None
    storage_method: StorageMethod | None
    storage_location: str | None
    contact_window: str | None
    closure_reason: str | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NewItem:
    """创建持久化记录所需、且已经过 Service 校验的数据。"""

    owner_id: int
    type: RecordType
    category: str
    title: str
    description: str
    location: str
    campus: Campus
    area: CampusArea | None
    occurred_at: datetime
    contact_hint: str
    contact: str
    contact_note: str | None
    storage_method: StorageMethod | None
    storage_location: str | None
    contact_window: str | None


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


@dataclass(frozen=True, slots=True)
class OwnedItemFilters:
    """“我的记录”查询使用的所有者、类型、状态和分页条件。"""

    owner_id: int
    item_type: RecordType | None
    status: ItemStatus | None
    offset: int
    limit: int


class ItemRepository(Protocol):
    """声明查询与管理业务需要的数据访问能力。"""

    def list_filtered(self, filters: ItemFilters) -> tuple[list[ItemRead], int]:
        """返回当前页记录和筛选后的总数。"""

    def get_by_id(self, item_id: int) -> ItemRecord | None:
        """按主键读取完整内部记录。"""

    def list_matching_candidates(self, *, source: ItemRecord, limit: int = 50) -> list[ItemRecord]:
        """返回同校区、相反类型的进行中候选，具体评分由 Service 负责。"""

    def count_by_status(self) -> dict[ItemStatus, int]:
        """返回管理端概览所需的状态计数。"""

    def create(self, item: NewItem) -> ItemRecord:
        """创建一条属于当前用户的记录。"""

    def list_owned(self, filters: OwnedItemFilters) -> tuple[list[ItemOwnerRead], int]:
        """查询某个用户拥有的记录。"""

    def update_fields(
        self,
        item_id: int,
        changes: dict[str, Any],
        *,
        expected_status: ItemStatus,
    ) -> ItemRecord:
        """更新 Service 已经校验并过滤的可编辑字段。"""

    def change_status(
        self,
        *,
        item_id: int,
        expected_status: ItemStatus,
        new_status: ItemStatus,
        reason: str | None,
        changed_by_id: int,
        changed_at: datetime,
    ) -> ItemRecord:
        """原子更新状态并写入审计记录。"""


class SqlAlchemyItemRepository:
    """使用 SQLAlchemy Session 查询和修改 MySQL 的正式仓储实现。"""

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

    def get_by_id(self, item_id: int) -> ItemRecord | None:
        """读取一条记录；是否允许查看由 Service 决定。"""

        item = self.session.get(Item, item_id)
        return self._to_record(item) if item else None

    def list_matching_candidates(self, *, source: ItemRecord, limit: int = 50) -> list[ItemRecord]:
        """预筛选相反类型候选，限制扫描数量避免发布接口无界查询。"""

        opposite = RecordType.FOUND if source.type == RecordType.LOST else RecordType.LOST
        rows = self.session.scalars(
            select(Item)
            .where(
                Item.id != source.id,
                Item.type == opposite.value,
                Item.status == ItemStatus.ACTIVE.value,
                Item.campus == source.campus.value,
            )
            .order_by(Item.occurred_at.desc(), Item.id.desc())
            .limit(limit)
        ).all()
        return [self._to_record(row) for row in rows]

    def count_by_status(self) -> dict[ItemStatus, int]:
        """使用一次分组查询生成全部物品状态统计。"""

        rows = self.session.execute(select(Item.status, func.count()).group_by(Item.status)).all()
        return {ItemStatus(status): count for status, count in rows}

    def create(self, item: NewItem) -> ItemRecord:
        """保存新记录并刷新数据库生成的编号和时间。"""

        row = Item(
            owner_id=item.owner_id,
            type=item.type.value,
            category=item.category,
            title=item.title,
            description=item.description,
            location=item.location,
            campus=item.campus.value,
            area=item.area.value if item.area else None,
            occurred_at=self._utc_naive(item.occurred_at),
            status=ItemStatus.ACTIVE.value,
            contact_hint=item.contact_hint,
            contact=item.contact,
            contact_note=item.contact_note,
            storage_method=item.storage_method.value if item.storage_method else None,
            storage_location=item.storage_location,
            contact_window=item.contact_window,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._to_record(row)

    def list_owned(self, filters: OwnedItemFilters) -> tuple[list[ItemOwnerRead], int]:
        """在数据库完成个人记录筛选、稳定排序和分页。"""

        statement = select(Item).where(Item.owner_id == filters.owner_id)
        if filters.item_type:
            statement = statement.where(Item.type == filters.item_type.value)
        if filters.status:
            statement = statement.where(Item.status == filters.status.value)

        total = (
            self.session.scalar(
                select(func.count()).select_from(statement.order_by(None).subquery())
            )
            or 0
        )
        rows = self.session.scalars(
            statement.order_by(Item.created_at.desc(), Item.id.desc())
            .offset(filters.offset)
            .limit(filters.limit)
        ).all()
        return [self._to_owner_schema(self._to_record(row)) for row in rows], total

    def update_fields(
        self,
        item_id: int,
        changes: dict[str, Any],
        *,
        expected_status: ItemStatus,
    ) -> ItemRecord:
        """只应用白名单字段，并拒绝读取后状态已经变化的并发更新。"""

        row = self.session.scalar(select(Item).where(Item.id == item_id).with_for_update())
        if row is None or row.status != expected_status.value:
            self.session.rollback()
            raise ConcurrentItemUpdateError
        for field, value in changes.items():
            if isinstance(value, Campus | CampusArea | StorageMethod):
                value = value.value
            if field == "occurred_at" and isinstance(value, datetime):
                value = self._utc_naive(value)
            setattr(row, field, value)
        self.session.commit()
        self.session.refresh(row)
        return self._to_record(row)

    def change_status(
        self,
        *,
        item_id: int,
        expected_status: ItemStatus,
        new_status: ItemStatus,
        reason: str | None,
        changed_by_id: int,
        changed_at: datetime,
    ) -> ItemRecord:
        """使用行锁保证状态修改和审计记录处于同一事务。"""

        row = self.session.scalar(select(Item).where(Item.id == item_id).with_for_update())
        if row is None or row.status != expected_status.value:
            self.session.rollback()
            raise ConcurrentItemUpdateError

        row.status = new_status.value
        row.closure_reason = reason
        row.closed_at = self._utc_naive(changed_at)
        self.session.add(
            ItemStatusHistory(
                item_id=item_id,
                changed_by_id=changed_by_id,
                old_status=expected_status.value,
                new_status=new_status.value,
                reason=reason,
                created_at=self._utc_naive(changed_at),
            )
        )
        self.session.commit()
        self.session.refresh(row)
        return self._to_record(row)

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

    @classmethod
    def _to_record(cls, item: Item) -> ItemRecord:
        """把 ORM 模型转换为与数据库实现解耦的内部记录。"""

        return ItemRecord(
            id=item.id,
            owner_id=item.owner_id,
            type=RecordType(item.type),
            category=item.category,
            title=item.title,
            description=item.description,
            location=item.location,
            campus=Campus(item.campus),
            area=CampusArea(item.area) if item.area else None,
            occurred_at=cls._as_utc(item.occurred_at),
            status=ItemStatus(item.status),
            contact_hint=item.contact_hint,
            contact=item.contact,
            contact_note=item.contact_note,
            storage_method=StorageMethod(item.storage_method) if item.storage_method else None,
            storage_location=item.storage_location,
            contact_window=item.contact_window,
            closure_reason=item.closure_reason,
            closed_at=cls._as_utc(item.closed_at) if item.closed_at else None,
            created_at=cls._as_utc(item.created_at),
            updated_at=cls._as_utc(item.updated_at),
        )

    @staticmethod
    def _to_owner_schema(item: ItemRecord) -> ItemOwnerRead:
        """构造仅供所有者或管理员查看的包含私密字段的响应。"""

        if item.owner_id is None or item.contact is None:
            raise ValueError("历史无归属记录不能转换为所有者视图")
        return ItemOwnerRead(
            id=item.id,
            owner_id=item.owner_id,
            type=item.type,
            category=item.category,
            title=item.title,
            description=item.description,
            location=item.location,
            campus=item.campus,
            area=item.area,
            occurred_at=item.occurred_at,
            status=item.status,
            contact_hint=item.contact_hint,
            contact=item.contact,
            contact_note=item.contact_note,
            storage_method=item.storage_method,
            storage_location=item.storage_location,
            contact_window=item.contact_window,
            closure_reason=item.closure_reason,
            closed_at=item.closed_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @staticmethod
    def _utc_naive(value: datetime) -> datetime:
        return value.astimezone(UTC).replace(tzinfo=None)


class InMemoryItemRepository:
    """不连接数据库的测试仓储，行为与正式仓储保持一致。"""

    def __init__(self, items: list[ItemRead] | None = None) -> None:
        # 旧列表测试传入公开 Schema；在内存中补成无归属的历史记录。
        self._items: dict[int, ItemRecord] = {
            item.id: ItemRecord(
                id=item.id,
                owner_id=None,
                type=item.type,
                category=item.category,
                title=item.title,
                description=item.description,
                location=item.location,
                campus=item.campus,
                area=item.area,
                occurred_at=item.occurred_at,
                status=item.status,
                contact_hint=item.contact_hint,
                contact=None,
                contact_note=None,
                storage_method=None,
                storage_location=None,
                contact_window=None,
                closure_reason=None,
                closed_at=None,
                created_at=item.occurred_at,
                updated_at=item.occurred_at,
            )
            for item in items or []
        }
        self._next_id = max(self._items, default=0) + 1
        self.status_history: list[tuple[int, ItemStatus, ItemStatus, int, str | None]] = []

    def list_filtered(self, filters: ItemFilters) -> tuple[list[ItemRead], int]:
        """在内存中执行等价筛选，供接口单元测试快速运行。"""

        items = [self._to_public(item) for item in self._items.values()]
        items = [item for item in items if item.status == filters.status]

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

    def get_by_id(self, item_id: int) -> ItemRecord | None:
        return self._items.get(item_id)

    def list_matching_candidates(self, *, source: ItemRecord, limit: int = 50) -> list[ItemRecord]:
        opposite = RecordType.FOUND if source.type == RecordType.LOST else RecordType.LOST
        candidates = [
            item
            for item in self._items.values()
            if item.id != source.id
            and item.type == opposite
            and item.status == ItemStatus.ACTIVE
            and item.campus == source.campus
        ]
        candidates.sort(key=lambda item: (item.occurred_at, item.id), reverse=True)
        return candidates[:limit]

    def count_by_status(self) -> dict[ItemStatus, int]:
        counts: dict[ItemStatus, int] = {}
        for item in self._items.values():
            counts[item.status] = counts.get(item.status, 0) + 1
        return counts

    def create(self, item: NewItem) -> ItemRecord:
        now = datetime.now(UTC)
        record = ItemRecord(
            id=self._next_id,
            owner_id=item.owner_id,
            type=item.type,
            category=item.category,
            title=item.title,
            description=item.description,
            location=item.location,
            campus=item.campus,
            area=item.area,
            occurred_at=item.occurred_at.astimezone(UTC),
            status=ItemStatus.ACTIVE,
            contact_hint=item.contact_hint,
            contact=item.contact,
            contact_note=item.contact_note,
            storage_method=item.storage_method,
            storage_location=item.storage_location,
            contact_window=item.contact_window,
            closure_reason=None,
            closed_at=None,
            created_at=now,
            updated_at=now,
        )
        self._items[record.id] = record
        self._next_id += 1
        return record

    def list_owned(self, filters: OwnedItemFilters) -> tuple[list[ItemOwnerRead], int]:
        records = [item for item in self._items.values() if item.owner_id == filters.owner_id]
        if filters.item_type:
            records = [item for item in records if item.type == filters.item_type]
        if filters.status:
            records = [item for item in records if item.status == filters.status]
        records.sort(key=lambda item: (item.created_at, item.id), reverse=True)
        total = len(records)
        page = records[filters.offset : filters.offset + filters.limit]
        return [SqlAlchemyItemRepository._to_owner_schema(item) for item in page], total

    def update_fields(
        self,
        item_id: int,
        changes: dict[str, Any],
        *,
        expected_status: ItemStatus,
    ) -> ItemRecord:
        record = self._items.get(item_id)
        if record is None or record.status != expected_status:
            raise ConcurrentItemUpdateError
        values = {field: getattr(record, field) for field in record.__dataclass_fields__}
        values.update(changes)
        values["updated_at"] = datetime.now(UTC)
        updated = ItemRecord(**values)
        self._items[item_id] = updated
        return updated

    def change_status(
        self,
        *,
        item_id: int,
        expected_status: ItemStatus,
        new_status: ItemStatus,
        reason: str | None,
        changed_by_id: int,
        changed_at: datetime,
    ) -> ItemRecord:
        record = self._items.get(item_id)
        if record is None or record.status != expected_status:
            raise ConcurrentItemUpdateError
        values = {field: getattr(record, field) for field in record.__dataclass_fields__}
        values.update(
            status=new_status,
            closure_reason=reason,
            closed_at=changed_at,
            updated_at=changed_at,
        )
        updated = ItemRecord(**values)
        self._items[item_id] = updated
        self.status_history.append((item_id, expected_status, new_status, changed_by_id, reason))
        return updated

    @staticmethod
    def _to_public(item: ItemRecord) -> ItemRead:
        return ItemRead(
            id=item.id,
            type=item.type,
            category=item.category,
            title=item.title,
            description=item.description,
            location=item.location,
            campus=item.campus,
            area=item.area,
            occurred_at=item.occurred_at,
            status=item.status,
            contact_hint=item.contact_hint,
        )

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
