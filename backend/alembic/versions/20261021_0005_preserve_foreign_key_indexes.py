"""为历史迁移的 MySQL 回滚保留独立外键索引。

Revision ID: 20261021_0005
Revises: 20261006_0004
Create Date: 2026-10-21

历史迁移先删除业务索引再删除表；MySQL 可能已经用这些业务索引替换了
自动生成的外键索引，导致 DROP INDEX 报错 1553。新增独立支撑索引，
无需改写已发布的迁移或关闭外键检查。
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import context, op

revision: str = "20261021_0005"
down_revision: str | Sequence[str] | None = "20261006_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SUPPORT_INDEXES = (
    ("stored_images", "ix_stored_images_owner_fk", ["owner_id"]),
    ("stored_images", "ix_stored_images_item_fk", ["item_id", "id"]),
    ("item_status_history", "ix_item_status_history_item_fk", ["item_id"]),
    ("auth_sessions", "ix_auth_sessions_user_fk", ["user_id"]),
    ("items", "ix_items_owner_fk", ["owner_id"]),
)


def upgrade() -> None:
    """补足索引；从旧版本重新升级时复用已保留的同名索引。"""

    inspector = None if context.is_offline_mode() else sa.inspect(op.get_bind())
    for table, name, columns in SUPPORT_INDEXES:
        existing = set() if inspector is None else {
            index["name"] for index in inspector.get_indexes(table)
        }
        if name not in existing:
            op.create_index(name, table, columns)


def downgrade() -> None:
    """刻意保留兼容索引，供 0004、0003、0002 的回滚使用。

    降到 0004 时只额外保留索引，不改变数据或约束。继续回滚时，历史迁移
    删除对应表会一并移除索引；再次升级由 upgrade 的存在性检查保证幂等。
    """
