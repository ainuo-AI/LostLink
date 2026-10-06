"""物品状态变化的数据库审计模型。

每次有效状态转换单独写入一条不可变记录，保存原状态、新状态、操作者、原因和
时间。该表服务于后续个人历史与管理员审计，不作为公开物品详情的一部分。
"""

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, String, text
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ItemStatusHistory(Base):
    """保存一次已经成功提交的物品状态转换。"""

    __tablename__ = "item_status_history"
    __table_args__ = (
        Index("ix_item_status_history_item_created", "item_id", "created_at"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("items.id", name="fk_item_status_history_item_id_items", ondelete="CASCADE"),
        nullable=False,
    )
    changed_by_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_item_status_history_changed_by_users"),
        nullable=False,
    )
    old_status: Mapped[str] = mapped_column(String(16), nullable=False)
    new_status: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
