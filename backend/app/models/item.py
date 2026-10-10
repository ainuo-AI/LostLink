"""失物与拾物记录的数据库模型。

这里表达 MySQL 持久化结构；公开 API 字段仍由 schemas/item.py 单独定义。
"""

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Item(Base):
    """保存一条失物或拾物记录。"""

    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("type IN ('lost', 'found')", name="ck_items_type"),
        CheckConstraint(
            "status IN ('active', 'recovered', 'returned', 'closed')",
            name="ck_items_status",
        ),
        CheckConstraint("campus IN ('东丽校区', '宁河校区')", name="ck_items_campus"),
        CheckConstraint(
            "(campus = '东丽校区' AND area IN ('北区', '南区')) "
            "OR (campus = '宁河校区' AND area IS NULL)",
            name="ck_items_campus_area",
        ),
        CheckConstraint(
            "storage_method IS NULL OR storage_method IN ('self', 'office')",
            name="ck_items_storage_method",
        ),
        Index("ix_items_status_occurred_id", "status", "occurred_at", "id"),
        Index("ix_items_type", "type"),
        Index("ix_items_category", "category"),
        Index("ix_items_campus_area", "campus", "area"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # 历史演示记录允许没有发布者；后续写入接口必须绑定当前登录用户。
    owner_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_items_owner_id_users", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(120), nullable=False)
    campus: Mapped[str] = mapped_column(String(20), nullable=False)
    area: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # MySQL DATETIME 不保存时区；项目约定写入和读取时都按 UTC 解释。
    occurred_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    contact_hint: Mapped[str] = mapped_column(String(255), nullable=False)
    # 发布者填写的联系方式直接展示在公开记录中；历史记录可能为空。
    contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # 下列字段只适用于 found；历史数据和 lost 记录保持为空。
    storage_method: Mapped[str | None] = mapped_column(String(16), nullable=True)
    storage_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_window: Mapped[str | None] = mapped_column(String(100), nullable=True)
    closure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        onupdate=func.current_timestamp(),
    )
