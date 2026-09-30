"""创建失物与拾物记录表。

Revision ID: 20260930_0001
Revises: None
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20260930_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """建立 items 表、业务约束和列表查询所需索引。"""

    op.create_table(
        "items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=120), nullable=False),
        sa.Column("campus", sa.String(length=20), nullable=False),
        sa.Column("area", sa.String(length=20), nullable=True),
        sa.Column("occurred_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("contact_hint", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.CheckConstraint("type IN ('lost', 'found')", name="ck_items_type"),
        sa.CheckConstraint(
            "status IN ('active', 'recovered', 'returned', 'closed')",
            name="ck_items_status",
        ),
        sa.CheckConstraint("campus IN ('东丽校区', '宁河校区')", name="ck_items_campus"),
        sa.CheckConstraint(
            "(campus = '东丽校区' AND area IN ('北区', '南区')) "
            "OR (campus = '宁河校区' AND area IS NULL)",
            name="ck_items_campus_area",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_items"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index("ix_items_type", "items", ["type"], unique=False)
    op.create_index("ix_items_category", "items", ["category"], unique=False)
    op.create_index("ix_items_campus_area", "items", ["campus", "area"], unique=False)
    op.create_index(
        "ix_items_status_occurred_id",
        "items",
        ["status", "occurred_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    """删除首版 items 表；仅用于尚未保存有效数据的开发环境回滚。"""

    op.drop_index("ix_items_status_occurred_id", table_name="items")
    op.drop_index("ix_items_campus_area", table_name="items")
    op.drop_index("ix_items_category", table_name="items")
    op.drop_index("ix_items_type", table_name="items")
    op.drop_table("items")
