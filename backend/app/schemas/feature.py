"""图片、举报、匹配通知与管理后台的公开 API 契约。

本模块集中定义新功能跨 HTTP 边界传输的数据结构。数据库 JSON 字符串会在
Repository 中解析为明确字段，避免前端依赖内部存储格式。
"""

from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.auth import UserRead, UserStatus
from app.schemas.item import ItemRead


class ImageRead(BaseModel):
    """上传成功后返回的图片元数据和访问地址。"""

    id: str
    content_type: str
    size_bytes: int = Field(ge=1)
    url: str
    created_at: datetime


class ReportStatus(StrEnum):
    """举报从待处理到管理员结案的状态。"""

    PENDING = "pending"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"
    CONTENT_HIDDEN = "content_hidden"


class ReportCreate(BaseModel):
    """用户举报一条物品记录时提交的原因和补充说明。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    reason: str = Field(min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=500)


class ReportResolve(BaseModel):
    """管理员处理举报时提交的结论和必填说明。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    status: ReportStatus
    resolution_note: str = Field(min_length=2, max_length=500)

    @model_validator(mode="after")
    def reject_pending_target(self) -> "ReportResolve":
        if self.status == ReportStatus.PENDING:
            raise ValueError("处理结果不能仍为 pending")
        return self


class ReportRead(BaseModel):
    """用户和管理员都可读取的举报摘要。"""

    id: int
    item_id: int
    reporter_id: int
    reason: str
    description: str | None
    status: ReportStatus
    resolution_note: str | None
    handled_by_id: int | None
    handled_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ReportListResponse(BaseModel):
    """举报列表分页响应。"""

    items: list[ReportRead]
    page: int
    page_size: int
    total: int


class MatchStatus(StrEnum):
    """候选匹配状态；confirmed 仅保留用于读取历史记录。"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class MatchDimension(BaseModel):
    """解释综合分数的单个匹配维度。"""

    label: str
    score: int | None = Field(default=None, ge=0, le=100)
    explanation: str


class MatchNotificationRead(BaseModel):
    """通知列表和匹配详情共享的完整候选视图。"""

    id: int
    title: str
    summary: str
    created_at: datetime
    is_read: bool
    status: MatchStatus
    mine: ItemRead
    candidate: ItemRead
    score: int = Field(ge=0, le=100)
    dimensions: list[MatchDimension]
    rejection_reason: str | None
    rejection_note: str | None


class MatchNotificationListResponse(BaseModel):
    """匹配通知分页响应，并单独提供未读数量。"""

    items: list[MatchNotificationRead]
    page: int
    page_size: int
    total: int
    unread: int


class MatchFeedback(BaseModel):
    """用户拒绝候选匹配；不再接受确认匹配请求。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    status: Literal[MatchStatus.REJECTED]
    reason: str | None = Field(default=None, max_length=100)
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_decision(self) -> "MatchFeedback":
        if not self.reason:
            raise ValueError("拒绝候选时必须填写原因")
        return self


class AdminUserListResponse(BaseModel):
    """管理端用户分页响应。"""

    items: list[UserRead]
    page: int
    page_size: int
    total: int


class UserStatusUpdate(BaseModel):
    """管理员限制或恢复普通用户账号。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    status: UserStatus
    reason: str = Field(min_length=2, max_length=500)


class OverviewRead(BaseModel):
    """管理台首页使用的核心运营计数。"""

    users_total: int
    users_restricted: int
    items_total: int
    items_active: int
    reports_pending: int
    notifications_unread: int


class AuditLogRead(BaseModel):
    """一次不可变管理员操作审计记录。"""

    id: int
    actor_id: int
    action: str
    object_type: str
    object_id: str
    reason: str
    details: dict[str, object] | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """审计日志分页响应。"""

    items: list[AuditLogRead]
    page: int
    page_size: int
    total: int


class CalibrationStatus(StrEnum):
    """候选权重版本的审核和上线状态。"""

    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class CalibrationTaskCreate(BaseModel):
    """创建一次指定日期范围的匹配校准任务。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    category: str | None = Field(default=None, max_length=50)
    range_start: date
    range_end: date

    @model_validator(mode="after")
    def validate_range(self) -> "CalibrationTaskCreate":
        if self.range_end < self.range_start:
            raise ValueError("结束日期不能早于开始日期")
        return self


class CalibrationTaskRead(BaseModel):
    """校准任务的执行结果和候选版本关联。"""

    id: int
    category: str | None
    range_start: date
    range_end: date
    status: str
    requested_by_id: int
    result_metrics: dict[str, float] | None
    candidate_version_id: int | None
    created_at: datetime
    completed_at: datetime | None


class CalibrationVersionRead(BaseModel):
    """可审核、启用或归档的匹配权重版本。"""

    id: int
    version_key: str
    status: CalibrationStatus
    weights: dict[str, float]
    metrics: dict[str, float]
    created_by_id: int
    reviewed_by_id: int | None
    review_reason: str | None
    created_at: datetime
    updated_at: datetime


class CalibrationVersionAction(BaseModel):
    """管理员对候选版本执行审批、拒绝、启用或回滚。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    action: str = Field(pattern=r"^(approve|reject|activate|rollback)$")
    reason: str = Field(min_length=2, max_length=500)
