# 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
# 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
"""图片、举报、匹配通知和管理功能的数据库模型。

本模块只描述持久化结构：上传文件的二进制内容保存在受控目录，数据库保存元数据；
举报、匹配、审计和校准分别使用独立表，避免把管理状态混入 ``items``。
公开字段和权限规则仍由 Schema、Service 与 API 层负责。
"""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# 文档对应：图2-2-2、图2-2-3、图2-2-4 的图片实体；表1-1 图片管理。
# 设计文档对应：图4-3 StoredImage 数据类；mapped_column 对应图中字段，ForeignKey 对应关联。
class StoredImage(Base):
    """保存上传图片的所有者、校验结果和磁盘定位信息。"""

    __tablename__ = "stored_images"
    __table_args__ = (
        Index("ix_stored_images_owner_created", "owner_id", "created_at"),
        Index("ix_stored_images_owner_fk", "owner_id"),
        Index("ix_stored_images_item_fk", "item_id", "id"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # 设计文档对应：图4-3 上传时可暂未关联物品，StoredImage 对应 Item 0..1。
    item_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("items.id", ondelete="CASCADE"), nullable=True, index=True
    )
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )


# 文档对应：图2-3 举报实体；图2-2-8 提交举报；图2-2-9 处理举报。
# 设计文档对应：图4-3 Report 数据类；mapped_column 对应图中字段，ForeignKey 对应关联。
class Report(Base):
    """保存用户对公开物品记录提交的举报及管理员处理结果。"""

    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'dismissed', 'resolved', 'content_hidden')",
            name="ck_reports_status",
        ),
        Index("ix_reports_status_created", "status", "created_at"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    reporter_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    resolution_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # 设计文档对应：图4-3 待处理举报尚无管理员，处理人关联允许为空。
    handled_by_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    handled_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )


# 文档对应：图2-3 候选通知实体；图2-2-6、图2-2-7、图2-2-10 的通知数据。
# 设计文档对应：图4-3 MatchNotification 数据类；mapped_column 对应图中字段，ForeignKey 对应关联。
class MatchNotification(Base):
    """保存一名用户可见的候选匹配、解释、已读和反馈状态。"""

    __tablename__ = "match_notifications"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'rejected')",
            name="ck_match_notifications_status",
        ),
        UniqueConstraint(
            "recipient_id",
            "source_item_id",
            "candidate_item_id",
            name="uq_match_notification_pair",
        ),
        Index("ix_match_notifications_user_created", "recipient_id", "created_at"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    recipient_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # 设计文档对应：图4-3 候选通知分别关联来源物品与候选物品。
    source_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    candidate_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    dimensions_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rejection_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rejection_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )


# 文档对应：图2-2-9、图2-2-9a、图2-2-9c 的审计记录实体。
# 设计文档对应：图4-3 AdminAuditLog 数据类；mapped_column 对应图中字段，ForeignKey 对应关联。
class AdminAuditLog(Base):
    """不可变记录管理员对举报、用户和校准版本执行的操作。"""

    __tablename__ = "admin_audit_logs"
    __table_args__ = (
        Index("ix_admin_audit_created", "created_at", "id"),
        Index("ix_admin_audit_object", "object_type", "object_id"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    object_type: Mapped[str] = mapped_column(String(32), nullable=False)
    object_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )


# 文档范围：校准任务和版本管理未纳入当前需求规格说明书；此处保留已有实现，不关联当前图表。
class CalibrationVersion(Base):
    """保存匹配权重版本及审核、启用和回滚所需的状态。"""

    __tablename__ = "calibration_versions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'approved', 'active', 'rejected', 'archived')",
            name="ck_calibration_versions_status",
        ),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    version_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    weights_json: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    reviewed_by_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    review_reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )


# 文档范围：校准任务和版本管理未纳入当前需求规格说明书；此处保留已有实现，不关联当前图表。
class CalibrationTask(Base):
    """保存一次可复现的匹配评估任务及其候选版本结果。"""

    __tablename__ = "calibration_tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'completed', 'failed')", name="ck_calibration_tasks_status"
        ),
        Index("ix_calibration_tasks_created", "created_at", "id"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    category: Mapped[str | None] = mapped_column(String(50))
    range_start: Mapped[date] = mapped_column(Date, nullable=False)
    range_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    requested_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    result_metrics_json: Mapped[str | None] = mapped_column(Text)
    candidate_version_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("calibration_versions.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6))
