"""物品查询、发布、编辑和状态闭环的业务编排层。

Service 负责默认筛选、权限、跨字段规则、状态转换和敏感字段边界，再委托
Repository 执行持久化。该模块不依赖 FastAPI，也不直接执行 SQL。
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from app.core.errors import AppError
from app.core.security import require_owner_or_admin
from app.repositories.feature_repository import FeatureRepository
from app.repositories.item_repository import (
    ConcurrentItemUpdateError,
    ItemFilters,
    ItemRecord,
    ItemRepository,
    NewItem,
    OwnedItemFilters,
)
from app.schemas.auth import UserRead
from app.schemas.item import (
    Campus,
    CampusArea,
    ItemCreate,
    ItemListResponse,
    ItemOwnerListResponse,
    ItemOwnerRead,
    ItemRead,
    ItemStatus,
    ItemStatusUpdate,
    ItemUpdate,
    RecordType,
)
from app.services.campus_distance import campus_distance_table

if TYPE_CHECKING:
    from app.services.feature_service import MatchingService


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


@dataclass(frozen=True, slots=True)
class OwnedItemQuery:
    """当前用户个人记录页的筛选和分页条件。"""

    item_type: RecordType | None = None
    status: ItemStatus | None = None
    page: int = 1
    page_size: int = 20


class ItemService:
    """编排公开查询和需要身份认证的记录管理规则。"""

    def __init__(
        self,
        repository: ItemRepository,
        feature_repository: FeatureRepository | None = None,
        matching_service: "MatchingService | None" = None,
    ) -> None:
        """注入物品仓储，并可选接入图片关联和匹配通知仓储。"""

        self.repository = repository
        self.feature_repository = feature_repository
        self.matching_service = matching_service

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

        if self.feature_repository:
            items = [self._with_images(item) for item in items]

        return ItemListResponse(
            items=items,
            page=query.page,
            page_size=query.page_size,
            total=total,
        )

    def get_public_item(self, item_id: int) -> ItemRead:
        """读取一条公开详情，任何状态都只返回公开字段。"""

        item = self.repository.get_by_id(item_id)
        if item is None:
            raise AppError(code="ITEM_NOT_FOUND", message="未找到该物品记录", status_code=404)
        public = self._to_public(item)
        return self._with_images(public) if self.feature_repository else public

    def create_item(
        self,
        payload: ItemCreate,
        user: UserRead,
        *,
        now: datetime | None = None,
    ) -> ItemOwnerRead:
        """发布一条自动归属于当前用户的 active 记录。"""

        current_time = now or datetime.now(UTC)
        if payload.occurred_at.astimezone(UTC) > current_time:
            raise AppError(
                code="ITEM_VALIDATION_ERROR",
                message="发生时间不能晚于当前时间",
                status_code=422,
            )
        self._validate_place_selection(payload.campus, payload.area, payload.location)
        if payload.type == RecordType.FOUND:
            self._validate_place_selection(
                payload.campus, None, payload.storage_location, storage=True
            )
        self._validate_images(payload.image_ids, owner_id=user.id)

        item = self.repository.create(
            NewItem(
                owner_id=user.id,
                type=payload.type,
                category=payload.category,
                title=payload.title,
                description=payload.description,
                location=payload.location,
                campus=payload.campus,
                area=payload.area,
                occurred_at=payload.occurred_at,
                contact_hint=self._contact_hint(payload.contact_note),
                contact=payload.contact.get_secret_value(),
                contact_note=payload.contact_note,
                storage_method=payload.storage_method,
                storage_location=payload.storage_location,
                contact_window=payload.contact_window,
            )
        )
        if self.feature_repository:
            # 图片已在创建前完成归属校验，这里只关联新生成的物品编号。
            self.feature_repository.attach_images(
                image_ids=payload.image_ids,
                item_id=item.id,
                owner_id=user.id,
            )
            # 延迟导入避免两个 Service 模块在加载阶段形成循环依赖。
            from app.services.feature_service import MatchingService

            matcher = self.matching_service or MatchingService(
                self.feature_repository, self.repository
            )
            matcher.generate_for_item(item)
        owner = self._to_owner(item)
        return self._with_images(owner) if self.feature_repository else owner

    def list_owned_items(
        self,
        query: OwnedItemQuery,
        user: UserRead,
    ) -> ItemOwnerListResponse:
        """返回当前用户自己的全部状态记录，不暴露其他用户数据。"""

        items, total = self.repository.list_owned(
            OwnedItemFilters(
                owner_id=user.id,
                item_type=query.item_type,
                status=query.status,
                offset=(query.page - 1) * query.page_size,
                limit=query.page_size,
            )
        )
        if self.feature_repository:
            items = [self._with_images(item) for item in items]
        return ItemOwnerListResponse(
            items=items,
            page=query.page,
            page_size=query.page_size,
            total=total,
        )

    def update_item(
        self,
        item_id: int,
        payload: ItemUpdate,
        user: UserRead,
        *,
        now: datetime | None = None,
    ) -> ItemOwnerRead:
        """允许发布者或管理员编辑仍处于 active 的记录。"""

        item = self._get_managed_item(item_id, user)
        if item.status != ItemStatus.ACTIVE:
            raise AppError(
                code="ITEM_NOT_EDITABLE",
                message="已结束的记录不能继续编辑",
                status_code=409,
            )

        provided = payload.model_dump(exclude_unset=True)
        if not provided:
            raise AppError(
                code="NO_CHANGES",
                message="请至少提供一个需要修改的字段",
                status_code=422,
            )
        image_ids = provided.pop("image_ids", None)
        if image_ids is not None:
            self._validate_images(image_ids, owner_id=user.id, item_id=item.id)
        if not provided and image_ids is None:
            raise AppError(
                code="NO_CHANGES",
                message="请至少提供一个需要修改的字段",
                status_code=422,
            )

        required_fields = {
            "category",
            "title",
            "description",
            "location",
            "campus",
            "occurred_at",
            "contact",
        }
        if any(field in provided and provided[field] is None for field in required_fields):
            raise AppError(
                code="ITEM_VALIDATION_ERROR",
                message="必填字段不能设置为空",
                status_code=422,
            )

        if "contact" in provided:
            provided["contact"] = provided["contact"].get_secret_value()
        self._validate_merged_update(item, provided, now=now or datetime.now(UTC))
        if "contact_note" in provided:
            provided["contact_hint"] = self._contact_hint(provided["contact_note"])

        try:
            updated = (
                self.repository.update_fields(item_id, provided, expected_status=item.status)
                if provided
                else item
            )
        except ConcurrentItemUpdateError as exc:
            raise AppError(
                code="ITEM_UPDATE_CONFLICT",
                message="记录已发生变化，请重新加载后再试",
                status_code=409,
            ) from exc
        if image_ids is not None and self.feature_repository:
            self.feature_repository.replace_item_images(
                image_ids=image_ids,
                item_id=item.id,
                owner_id=user.id,
            )
        owner = self._to_owner(updated)
        return self._with_images(owner) if self.feature_repository else owner

    def update_status(
        self,
        item_id: int,
        payload: ItemStatusUpdate,
        user: UserRead,
        *,
        now: datetime | None = None,
    ) -> ItemOwnerRead:
        """执行合法终态转换，并在同一事务中写入状态审计。"""

        item = self._get_managed_item(item_id, user)
        self._validate_status_transition(item, payload.status)
        try:
            updated = self.repository.change_status(
                item_id=item.id,
                expected_status=item.status,
                new_status=payload.status,
                reason=payload.reason,
                changed_by_id=user.id,
                changed_at=now or datetime.now(UTC),
            )
        except ConcurrentItemUpdateError as exc:
            raise AppError(
                code="ITEM_UPDATE_CONFLICT",
                message="记录状态已变化，请重新加载后再试",
                status_code=409,
            ) from exc
        owner = self._to_owner(updated)
        return self._with_images(owner) if self.feature_repository else owner

    def _get_managed_item(self, item_id: int, user: UserRead) -> ItemRecord:
        """读取管理对象并统一执行存在性和资源归属检查。"""

        item = self.repository.get_by_id(item_id)
        if item is None:
            raise AppError(code="ITEM_NOT_FOUND", message="未找到该物品记录", status_code=404)
        require_owner_or_admin(user, item)
        return item

    @staticmethod
    def _validate_place_selection(campus, area, name, *, storage: bool = False) -> None:
        if not campus_distance_table().is_selection(campus, area, name, any_area=storage):
            raise AppError(
                code="ITEM_LOCATION_INVALID",
                message=(
                    "请从所选校区的保管地点选项中选择。" if storage
                    else "请从所选校区和区域的地点选项中选择。"
                ),
                status_code=422,
            )

    @staticmethod
    def _validate_merged_update(
        item: ItemRecord,
        changes: dict[str, object],
        *,
        now: datetime,
    ) -> None:
        """将部分更新与原记录合并后检查跨字段业务规则。"""

        campus = changes.get("campus", item.campus)
        area = changes.get("area", item.area)
        if campus == Campus.DONGLI and area is None:
            raise AppError(
                code="ITEM_VALIDATION_ERROR",
                message="东丽校区必须选择北区或南区",
                status_code=422,
            )
        if campus == Campus.NINGHE and area is not None:
            raise AppError(
                code="ITEM_VALIDATION_ERROR",
                message="宁河校区不能设置二级区域",
                status_code=422,
            )

        ItemService._validate_place_selection(
            campus, area, changes.get("location", item.location)
        )
        if item.type == RecordType.FOUND:
            ItemService._validate_place_selection(
                campus, None, changes.get("storage_location", item.storage_location), storage=True
            )

        occurred_at = changes.get("occurred_at", item.occurred_at)
        if isinstance(occurred_at, datetime) and occurred_at.astimezone(UTC) > now:
            raise AppError(
                code="ITEM_VALIDATION_ERROR",
                message="发生时间不能晚于当前时间",
                status_code=422,
            )

        storage_method = changes.get("storage_method", item.storage_method)
        storage_location = changes.get("storage_location", item.storage_location)
        contact_window = changes.get("contact_window", item.contact_window)
        storage_values = (storage_method, storage_location, contact_window)
        if item.type == RecordType.FOUND and any(value is None for value in storage_values):
            raise AppError(
                code="ITEM_VALIDATION_ERROR",
                message="拾物记录必须保留完整保管信息",
                status_code=422,
            )
        if item.type == RecordType.LOST and any(value is not None for value in storage_values):
            raise AppError(
                code="ITEM_VALIDATION_ERROR",
                message="失物记录不能填写拾物保管信息",
                status_code=422,
            )

    @staticmethod
    def _validate_status_transition(item: ItemRecord, new_status: ItemStatus) -> None:
        """第一阶段只允许进行中记录进入与类型匹配的终态。"""

        if item.status != ItemStatus.ACTIVE:
            raise AppError(
                code="INVALID_STATUS_TRANSITION",
                message="该记录已经结束，不能重复修改状态",
                status_code=409,
            )
        allowed = {ItemStatus.CLOSED}
        allowed.add(ItemStatus.RECOVERED if item.type == RecordType.LOST else ItemStatus.RETURNED)
        if new_status not in allowed:
            raise AppError(
                code="INVALID_STATUS_TRANSITION",
                message="目标状态不适用于该记录",
                status_code=409,
            )

    def _validate_images(
        self,
        image_ids: list[str],
        *,
        owner_id: int,
        item_id: int | None = None,
    ) -> None:
        """确认图片存在、属于当前用户，并且没有被其他物品占用。"""

        if len(set(image_ids)) != len(image_ids):
            raise AppError(
                code="DUPLICATE_IMAGE",
                message="不能重复关联同一张图片",
                status_code=422,
            )
        if not image_ids:
            return
        if self.feature_repository is None:
            raise AppError(
                code="IMAGES_UNAVAILABLE",
                message="图片服务暂不可用",
                status_code=503,
            )
        for image_id in image_ids:
            image = self.feature_repository.get_image(image_id)
            if image is None or image.owner_id != owner_id or image.item_id not in (None, item_id):
                raise AppError(
                    code="IMAGE_NOT_AVAILABLE",
                    message="图片不存在、无权使用或已被其他物品关联",
                    status_code=422,
                )

    @staticmethod
    def _contact_hint(note: str | None) -> str:
        """公开响应只给出联系说明，不泄露完整手机号或邮箱。"""

        return note or "联系方式已保护，请先核验物品特征。"

    def _with_images(self, item: ItemRead) -> ItemRead:
        """把数据库图片编号转换为前端可直接访问的稳定 URL。"""

        assert self.feature_repository is not None
        urls = [
            f"/api/v1/uploads/images/{image.id}"
            for image in self.feature_repository.list_item_images(item.id)
        ]
        return item.model_copy(update={"image_urls": urls})

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
    def _to_owner(item: ItemRecord) -> ItemOwnerRead:
        if item.owner_id is None or item.contact is None:
            raise AppError(
                code="ITEM_NOT_MANAGEABLE",
                message="历史记录缺少发布者信息，不能执行管理操作",
                status_code=409,
            )
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
