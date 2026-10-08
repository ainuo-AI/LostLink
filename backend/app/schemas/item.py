"""失物与拾物记录的 API 请求、响应和枚举契约。

Schema 与数据库模型保持分离，防止未来数据库内部字段被意外暴露给前端。
公开详情只包含可展示字段；发布者视图才包含联系方式和管理字段。
"""

import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator


class RecordType(StrEnum):
    """记录类型：用户丢失的物品或用户拾到的物品。"""

    LOST = "lost"
    FOUND = "found"


class Campus(StrEnum):
    """第一阶段支持的校区。"""

    DONGLI = "东丽校区"
    NINGHE = "宁河校区"


class CampusArea(StrEnum):
    """东丽校区的二级区域。"""

    NORTH = "北区"
    SOUTH = "南区"


class ItemStatus(StrEnum):
    """记录状态，对应进行中、已找回、已归还和已关闭。"""

    ACTIVE = "active"
    RECOVERED = "recovered"
    RETURNED = "returned"
    CLOSED = "closed"


class CampusLocationOption(BaseModel):
    """发布和编辑共用的校园地点选项，不返回坐标与距离矩阵。"""

    id: str
    name: str
    campus: Campus
    area: CampusArea | None
    simulated: bool


class StorageMethod(StrEnum):
    """拾物记录的保管方式。"""

    SELF = "self"
    OFFICE = "office"


def _validate_location_rules(
    *,
    campus: Campus | None,
    area: CampusArea | None,
) -> None:
    """校验校区与二级区域的组合，与数据库约束保持一致。"""

    if campus == Campus.DONGLI and area is None:
        raise ValueError("东丽校区必须选择北区或南区")
    if campus == Campus.NINGHE and area is not None:
        raise ValueError("宁河校区不能设置二级区域")


def _validate_found_fields(
    *,
    item_type: RecordType,
    storage_method: StorageMethod | None,
    storage_location: str | None,
    contact_window: str | None,
) -> None:
    """拾物记录必须说明保管方式；失物记录不能携带拾物专属字段。"""

    found_values = (storage_method, storage_location, contact_window)
    if item_type == RecordType.FOUND and any(value is None for value in found_values):
        raise ValueError("拾物记录必须填写保管方式、保管地点和可联系时间")
    if item_type == RecordType.LOST and any(value is not None for value in found_values):
        raise ValueError("失物记录不能填写拾物保管信息")


class ItemRead(BaseModel):
    """前端可以安全展示的一条失物或拾物记录。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: RecordType
    category: str
    title: str
    description: str
    location: str
    campus: Campus
    area: CampusArea | None = None
    occurred_at: datetime
    status: ItemStatus
    contact_hint: str
    image_urls: list[str] = Field(default_factory=list)


class ItemListResponse(BaseModel):
    """统一的分页列表响应。"""

    items: list[ItemRead]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)


class ItemCreate(BaseModel):
    """发布失物或拾物时由前端提交的字段。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    type: RecordType
    category: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=2, max_length=60)
    description: str = Field(min_length=10, max_length=500)
    location: str = Field(min_length=2, max_length=100)
    campus: Campus
    area: CampusArea | None = None
    occurred_at: datetime
    contact: SecretStr = Field(min_length=5, max_length=255)
    contact_note: str | None = Field(default=None, max_length=200)
    storage_method: StorageMethod | None = None
    storage_location: str | None = Field(default=None, min_length=2, max_length=100)
    contact_window: str | None = Field(default=None, min_length=2, max_length=100)
    image_ids: list[str] = Field(default_factory=list, max_length=3)

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        """拒绝没有时区的信息，避免前后端把本地时间误当 UTC。"""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("时间必须包含时区")
        return value

    @field_validator("contact")
    @classmethod
    def validate_contact(cls, value: SecretStr) -> SecretStr:
        """当前支持中国大陆手机号或电子邮箱。"""

        contact = value.get_secret_value().strip()
        phone_valid = (
            len(contact) == 11
            and contact.isdigit()
            and contact.startswith("1")
            and contact[1] in "3456789"
        )
        email_valid = re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", contact) is not None
        if not phone_valid and not email_valid:
            raise ValueError("请输入有效的中国大陆手机号或电子邮箱")
        return SecretStr(contact)

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "ItemCreate":
        """执行无法由单字段约束表达的业务组合校验。"""

        _validate_location_rules(campus=self.campus, area=self.area)
        _validate_found_fields(
            item_type=self.type,
            storage_method=self.storage_method,
            storage_location=self.storage_location,
            contact_window=self.contact_window,
        )
        return self


class ItemUpdate(BaseModel):
    """发布者可编辑的字段；未提供字段与显式 ``null`` 保持区分。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    category: str | None = Field(default=None, min_length=1, max_length=50)
    title: str | None = Field(default=None, min_length=2, max_length=60)
    description: str | None = Field(default=None, min_length=10, max_length=500)
    location: str | None = Field(default=None, min_length=2, max_length=100)
    campus: Campus | None = None
    area: CampusArea | None = None
    occurred_at: datetime | None = None
    contact: SecretStr | None = Field(default=None, min_length=5, max_length=255)
    contact_note: str | None = Field(default=None, max_length=200)
    storage_method: StorageMethod | None = None
    storage_location: str | None = Field(default=None, min_length=2, max_length=100)
    contact_window: str | None = Field(default=None, min_length=2, max_length=100)
    image_ids: list[str] | None = Field(default=None, max_length=3)

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("时间必须包含时区")
        return value

    @field_validator("contact")
    @classmethod
    def validate_contact(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return None
        # 复用创建请求的联系方式规则，保持新增和编辑行为一致。
        return ItemCreate.validate_contact(value)


class ItemStatusUpdate(BaseModel):
    """发布者关闭或完成一条记录时提交的状态变化。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    status: ItemStatus
    reason: str | None = Field(default=None, max_length=255)


class ItemOwnerRead(ItemRead):
    """仅向发布者或管理员返回的记录管理视图。"""

    owner_id: int
    contact: str
    contact_note: str | None
    storage_method: StorageMethod | None
    storage_location: str | None
    contact_window: str | None
    closure_reason: str | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ItemOwnerListResponse(BaseModel):
    """“我的记录”使用的稳定分页响应。"""

    items: list[ItemOwnerRead]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
