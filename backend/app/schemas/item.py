"""失物与拾物记录的公开数据结构。

Schema 与数据库模型保持分离，防止未来数据库内部字段被意外暴露给前端。
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


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


class ItemListResponse(BaseModel):
    """统一的分页列表响应。"""

    items: list[ItemRead]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
