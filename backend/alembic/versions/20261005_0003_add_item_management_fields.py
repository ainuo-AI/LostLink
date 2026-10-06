"""增加物品管理私密字段和状态审计表。

本 migration 让认证用户能够发布、编辑和关闭记录。新增字段全部允许历史演示
数据为空；新写入数据的必填规则由 Schema、Service 和自动测试共同保证。

Revision ID: 20261005_0003
Revises: 20261005_0002
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261005_0003"
down_revision: str | Sequence[str] | None = "20261005_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """扩展 items，并创建不可变状态变化记录。"""

    op.add_column("items", sa.Column("contact", sa.String(length=255), nullable=True))
    op.add_column("items", sa.Column("contact_note", sa.String(length=200), nullable=True))
    op.add_column("items", sa.Column("storage_method", sa.String(length=16), nullable=True))
    op.add_column("items", sa.Column("storage_location", sa.String(length=100), nullable=True))
    op.add_column("items", sa.Column("contact_window", sa.String(length=100), nullable=True))
    op.add_column("items", sa.Column("closure_reason", sa.String(length=255), nullable=True))
    op.add_column("items", sa.Column("closed_at", mysql.DATETIME(fsp=6), nullable=True))
    op.create_check_constraint(
        "ck_items_storage_method",
        "items",
        "storage_method IS NULL OR storage_method IN ('self', 'office')",
    )

    op.create_table(
        "item_status_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.BigInteger(), nullable=False),
        sa.Column("changed_by_id", sa.BigInteger(), nullable=False),
        sa.Column("old_status", sa.String(length=16), nullable=False),
        sa.Column("new_status", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_id"],
            ["users.id"],
            name="fk_item_status_history_changed_by_users",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["items.id"],
            name="fk_item_status_history_item_id_items",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_item_status_history"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_item_status_history_item_created",
        "item_status_history",
        ["item_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """移除状态审计表和物品管理私密字段。"""

    op.drop_index("ix_item_status_history_item_created", table_name="item_status_history")
    op.drop_table("item_status_history")
    op.drop_constraint("ck_items_storage_method", "items", type_="check")
    op.drop_column("items", "closed_at")
    op.drop_column("items", "closure_reason")
    op.drop_column("items", "contact_window")
    op.drop_column("items", "storage_location")
    op.drop_column("items", "storage_method")
    op.drop_column("items", "contact_note")
    op.drop_column("items", "contact")
