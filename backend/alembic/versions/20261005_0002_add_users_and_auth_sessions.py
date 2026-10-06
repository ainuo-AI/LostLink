"""增加用户、认证会话和物品归属字段。

本 migration 负责建立认证所需的持久化结构，并以可空 ``owner_id`` 兼容已有
演示物品。后续物品写入接口应在应用层强制关联当前用户，而不是把历史数据
迁移伪装成某个用户发布的记录。

Revision ID: 20261005_0002
Revises: 20260930_0001
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261005_0002"
down_revision: str | Sequence[str] | None = "20260930_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建认证数据结构，并为已有物品增加可空的发布者归属。"""

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("account", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=50), nullable=True),
        sa.Column("role", sa.String(length=16), server_default="user", nullable=False),
        sa.Column("status", sa.String(length=16), server_default="active", nullable=False),
        sa.Column("campus_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("locked_until", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column("last_login_at", mysql.DATETIME(fsp=6), nullable=True),
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
        sa.CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),
        sa.CheckConstraint("status IN ('active', 'restricted')", name="ck_users_status"),
        sa.CheckConstraint("failed_login_attempts >= 0", name="ck_users_failed_login_attempts"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("account", name="uq_users_account"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", mysql.DATETIME(fsp=6), nullable=False),
        sa.Column("revoked_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_auth_sessions_user_id_users", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_auth_sessions"),
        sa.UniqueConstraint("token_hash", name="uq_auth_sessions_token_hash"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_auth_sessions_user_expires",
        "auth_sessions",
        ["user_id", "expires_at"],
        unique=False,
    )

    # 已有 items 没有可靠发布者，先以可空字段进行兼容迁移，避免伪造归属。
    op.add_column("items", sa.Column("owner_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_items_owner_id_users",
        "items",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_items_owner_id", "items", ["owner_id"], unique=False)


def downgrade() -> None:
    """移除物品归属、会话和用户表。"""

    op.drop_index("ix_items_owner_id", table_name="items")
    op.drop_constraint("fk_items_owner_id_users", "items", type_="foreignkey")
    op.drop_column("items", "owner_id")
    op.drop_index("ix_auth_sessions_user_expires", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_table("users")
