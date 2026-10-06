"""增加图片、举报、匹配通知、管理审计和校准表。

Revision ID: 20261006_0004
Revises: 20261005_0003
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20261006_0004"
down_revision: str | Sequence[str] | None = "20261005_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> tuple[sa.Column, sa.Column]:
    """返回新业务表共用的微秒级创建与更新时间列。"""

    return (
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
    )


def upgrade() -> None:
    """创建前端剩余功能需要的六张持久化表和查询索引。"""

    op.create_table(
        "stored_images",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("item_id", sa.BigInteger(), nullable=True),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name="fk_stored_images_owner_users", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["items.id"], name="fk_stored_images_item_items", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_stored_images"),
        sa.UniqueConstraint("storage_key", name="uq_stored_images_storage_key"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index("ix_stored_images_item_id", "stored_images", ["item_id"])
    op.create_index("ix_stored_images_owner_created", "stored_images", ["owner_id", "created_at"])

    op.create_table(
        "reports",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.BigInteger(), nullable=False),
        sa.Column("reporter_id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("status", sa.String(24), server_default="pending", nullable=False),
        sa.Column("resolution_note", sa.String(500), nullable=True),
        sa.Column("handled_by_id", sa.BigInteger(), nullable=True),
        sa.Column("handled_at", mysql.DATETIME(fsp=6), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('pending', 'dismissed', 'resolved', 'content_hidden')",
            name="ck_reports_status",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["items.id"], name="fk_reports_item_items", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["reporter_id"], ["users.id"], name="fk_reports_reporter_users", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["handled_by_id"], ["users.id"], name="fk_reports_handler_users"),
        sa.PrimaryKeyConstraint("id", name="pk_reports"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index("ix_reports_status_created", "reports", ["status", "created_at"])

    op.create_table(
        "match_notifications",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("recipient_id", sa.BigInteger(), nullable=False),
        sa.Column("source_item_id", sa.BigInteger(), nullable=False),
        sa.Column("candidate_item_id", sa.BigInteger(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("dimensions_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("rejection_reason", sa.String(100), nullable=True),
        sa.Column("rejection_note", sa.String(500), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'rejected')", name="ck_match_notifications_status"
        ),
        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["users.id"],
            name="fk_match_notifications_recipient_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_item_id"],
            ["items.id"],
            name="fk_match_notifications_source_items",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_item_id"],
            ["items.id"],
            name="fk_match_notifications_candidate_items",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_match_notifications"),
        sa.UniqueConstraint(
            "recipient_id", "source_item_id", "candidate_item_id", name="uq_match_notification_pair"
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index(
        "ix_match_notifications_user_created", "match_notifications", ["recipient_id", "created_at"]
    )

    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("actor_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("object_type", sa.String(32), nullable=False),
        sa.Column("object_id", sa.String(64), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], name="fk_admin_audit_actor_users"),
        sa.PrimaryKeyConstraint("id", name="pk_admin_audit_logs"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index("ix_admin_audit_created", "admin_audit_logs", ["created_at", "id"])
    op.create_index("ix_admin_audit_object", "admin_audit_logs", ["object_type", "object_id"])

    op.create_table(
        "calibration_versions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("version_key", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), server_default="draft", nullable=False),
        sa.Column("weights_json", sa.Text(), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=False),
        sa.Column("created_by_id", sa.BigInteger(), nullable=False),
        sa.Column("reviewed_by_id", sa.BigInteger(), nullable=True),
        sa.Column("review_reason", sa.String(500), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'active', 'rejected', 'archived')",
            name="ck_calibration_versions_status",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name="fk_calibration_versions_creator_users"
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_id"], ["users.id"], name="fk_calibration_versions_reviewer_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_calibration_versions"),
        sa.UniqueConstraint("version_key", name="uq_calibration_versions_version_key"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )

    op.create_table(
        "calibration_tasks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("range_start", sa.Date(), nullable=False),
        sa.Column("range_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), server_default="queued", nullable=False),
        sa.Column("requested_by_id", sa.BigInteger(), nullable=False),
        sa.Column("result_metrics_json", sa.Text(), nullable=True),
        sa.Column("candidate_version_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            mysql.DATETIME(fsp=6),
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
            nullable=False,
        ),
        sa.Column("completed_at", mysql.DATETIME(fsp=6), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued', 'completed', 'failed')", name="ck_calibration_tasks_status"
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_id"], ["users.id"], name="fk_calibration_tasks_requester_users"
        ),
        sa.ForeignKeyConstraint(
            ["candidate_version_id"],
            ["calibration_versions.id"],
            name="fk_calibration_tasks_version",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_calibration_tasks"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_index("ix_calibration_tasks_created", "calibration_tasks", ["created_at", "id"])


def downgrade() -> None:
    """按外键依赖的逆序移除新增表。"""

    op.drop_index("ix_calibration_tasks_created", table_name="calibration_tasks")
    op.drop_table("calibration_tasks")
    op.drop_table("calibration_versions")
    op.drop_index("ix_admin_audit_object", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_created", table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")
    op.drop_index("ix_match_notifications_user_created", table_name="match_notifications")
    op.drop_table("match_notifications")
    op.drop_index("ix_reports_status_created", table_name="reports")
    op.drop_table("reports")
    op.drop_index("ix_stored_images_owner_created", table_name="stored_images")
    op.drop_index("ix_stored_images_item_id", table_name="stored_images")
    op.drop_table("stored_images")
