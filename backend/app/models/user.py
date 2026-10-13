# 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
# 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
"""用户账号与服务端会话的 SQLAlchemy 持久化模型。

``User`` 保存身份、角色、状态和登录保护字段；``AuthSession`` 保存可过期、
可吊销的会话令牌摘要。模型只表达数据库结构与关系，不直接作为 API 响应，
也不在模型方法中执行登录或权限业务规则。
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


# 文档对应：图2-3 用户实体；图2-2-1、图2-2-1a、图2-2-9a 的用户数据。
# 设计文档对应：图4-3 User 数据类；mapped_column 对应图中字段，ForeignKey 对应关联。
class User(Base):
    """保存本地账号、权限和登录保护状态。

    ``campus_verified`` 与账号能否登录分开保存：当前本地注册可以建立账号，
    但不会被误认为已经通过学校身份系统验证。
    """

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),
        CheckConstraint("status IN ('active', 'restricted')", name="ck_users_status"),
        CheckConstraint("failed_login_attempts >= 0", name="ck_users_failed_login_attempts"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="user")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    campus_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        server_onupdate=text("CURRENT_TIMESTAMP(6)"),
    )

    sessions: Mapped[list["AuthSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# 文档对应：图2-2-1 建立会话；图2-2-1b 结束会话；表1-1 用户与会话。
# 设计文档对应：图4-3 AuthSession 数据类；mapped_column 对应图中字段，ForeignKey 对应关联。
class AuthSession(Base):
    """保存不可逆的会话令牌摘要和服务端吊销状态。

    客户端持有的原始 Bearer 令牌不会写入数据库；查询时先计算 SHA-256 摘要，
    再与 ``token_hash`` 匹配。
    """

    __tablename__ = "auth_sessions"
    __table_args__ = (
        Index("ix_auth_sessions_user_expires", "user_id", "expires_at"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_0900_ai_ci"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # 设计文档对应：图4-3 User 1 对应 AuthSession 0..*；user_id 是关联外键。
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", name="fk_auth_sessions_user_id_users", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DATETIME(fsp=6), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )

    user: Mapped[User] = relationship(back_populates="sessions")
