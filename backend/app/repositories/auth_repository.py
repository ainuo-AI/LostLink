"""认证数据访问边界及其 SQLAlchemy、内存实现。

``AuthRepository`` 声明 Service 所需的最小持久化能力；
``SqlAlchemyAuthRepository`` 负责 MySQL 事务、唯一约束和时间转换；
``InMemoryAuthRepository`` 让接口测试无需连接个人数据库。

本模块不判断密码是否正确，也不决定谁具有管理员权限，这些业务规则由
``AuthService`` 和 ``core.security`` 负责。
"""

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import AuthSession, User
from app.schemas.auth import UserRole, UserStatus


class DuplicateAccountError(Exception):
    """把数据库唯一约束冲突转换为不依赖 SQLAlchemy 的仓储错误。"""


@dataclass(frozen=True, slots=True)
class UserRecord:
    """认证业务使用的内部用户记录，包含不会对外返回的密码摘要。

    Service 依赖该内部类型而非 SQLAlchemy ``User``，防止数据库字段意外成为
    公开 API 契约。
    """

    id: int
    account: str
    password_hash: str
    display_name: str | None
    role: UserRole
    status: UserStatus
    campus_verified: bool
    failed_login_attempts: int
    locked_until: datetime | None
    created_at: datetime


class AuthRepository(Protocol):
    """认证 Service 依赖的持久化能力。"""

    def get_user_by_account(self, account: str) -> UserRecord | None: ...

    def get_user_by_id(self, user_id: int) -> UserRecord | None: ...

    def list_users(
        self, *, keyword: str | None, status: UserStatus | None, offset: int, limit: int
    ) -> tuple[list[UserRecord], int]: ...

    def set_user_status(self, *, user_id: int, status: UserStatus) -> UserRecord | None: ...

    def create_user(
        self, *, account: str, password_hash: str, display_name: str | None
    ) -> UserRecord: ...

    def create_session(self, *, user_id: int, token_hash: str, expires_at: datetime) -> None: ...

    def get_user_by_active_session(
        self, *, token_hash: str, now: datetime
    ) -> UserRecord | None: ...

    def revoke_session(self, *, token_hash: str, now: datetime) -> bool: ...

    def record_login_failure(
        self, *, user_id: int, now: datetime, max_attempts: int, lock_minutes: int
    ) -> None: ...

    def record_login_success(self, *, user_id: int, now: datetime) -> None: ...


def _as_utc(value: datetime | None) -> datetime | None:
    """把 MySQL 无时区时间恢复为项目约定的 UTC 时间。"""

    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _to_record(user: User) -> UserRecord:
    return UserRecord(
        id=user.id,
        account=user.account,
        password_hash=user.password_hash,
        display_name=user.display_name,
        role=UserRole(user.role),
        status=UserStatus(user.status),
        campus_verified=user.campus_verified,
        failed_login_attempts=user.failed_login_attempts,
        locked_until=_as_utc(user.locked_until),
        created_at=_as_utc(user.created_at),
    )


def _utc_naive(value: datetime) -> datetime:
    """写入 MySQL DATETIME 前移除时区，但始终按 UTC 解释。"""

    return value.astimezone(UTC).replace(tzinfo=None)


class SqlAlchemyAuthRepository:
    """使用 SQLAlchemy Session 在 MySQL 中持久化用户和会话。"""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user_by_account(self, account: str) -> UserRecord | None:
        user = self.session.scalar(select(User).where(User.account == account))
        return _to_record(user) if user else None

    def get_user_by_id(self, user_id: int) -> UserRecord | None:
        """按编号读取用户，供管理端执行状态变更前的权限校验。"""

        user = self.session.get(User, user_id)
        return _to_record(user) if user else None

    def list_users(
        self, *, keyword: str | None, status: UserStatus | None, offset: int, limit: int
    ) -> tuple[list[UserRecord], int]:
        """在数据库中筛选并分页返回管理端用户列表。"""

        statement = select(User)
        if keyword and (cleaned := keyword.strip()):
            escaped = cleaned.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            statement = statement.where(
                (User.account.like(pattern, escape="\\"))
                | (User.display_name.like(pattern, escape="\\"))
            )
        if status:
            statement = statement.where(User.status == status.value)
        total = (
            self.session.scalar(
                select(func.count()).select_from(statement.order_by(None).subquery())
            )
            or 0
        )
        rows = self.session.scalars(
            statement.order_by(User.created_at.desc(), User.id.desc()).offset(offset).limit(limit)
        ).all()
        return [_to_record(row) for row in rows], total

    def set_user_status(self, *, user_id: int, status: UserStatus) -> UserRecord | None:
        """锁定目标用户行并更新账号状态。"""

        user = self.session.scalar(select(User).where(User.id == user_id).with_for_update())
        if user is None:
            self.session.rollback()
            return None
        user.status = status.value
        self.session.commit()
        self.session.refresh(user)
        return _to_record(user)

    def create_user(
        self, *, account: str, password_hash: str, display_name: str | None
    ) -> UserRecord:
        user = User(account=account, password_hash=password_hash, display_name=display_name)
        self.session.add(user)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateAccountError from exc
        self.session.refresh(user)
        return _to_record(user)

    def create_session(self, *, user_id: int, token_hash: str, expires_at: datetime) -> None:
        self.session.add(
            AuthSession(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=_utc_naive(expires_at),
            )
        )
        self.session.commit()

    def get_user_by_active_session(self, *, token_hash: str, now: datetime) -> UserRecord | None:
        statement = (
            select(User)
            .join(AuthSession, AuthSession.user_id == User.id)
            .where(
                AuthSession.token_hash == token_hash,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > _utc_naive(now),
            )
        )
        user = self.session.scalar(statement)
        return _to_record(user) if user else None

    def revoke_session(self, *, token_hash: str, now: datetime) -> bool:
        result = self.session.execute(
            update(AuthSession)
            .where(AuthSession.token_hash == token_hash, AuthSession.revoked_at.is_(None))
            .values(revoked_at=_utc_naive(now))
        )
        self.session.commit()
        return bool(result.rowcount)

    def record_login_failure(
        self, *, user_id: int, now: datetime, max_attempts: int, lock_minutes: int
    ) -> None:
        # 锁定用户行，避免并发失败请求互相覆盖计数而绕过临时锁定策略。
        user = self.session.scalar(select(User).where(User.id == user_id).with_for_update())
        if not user:
            return
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= max_attempts:
            user.locked_until = _utc_naive(now + timedelta(minutes=lock_minutes))
            user.failed_login_attempts = 0
        self.session.commit()

    def record_login_success(self, *, user_id: int, now: datetime) -> None:
        # 与失败更新使用相同的行锁，确保成功重置不会和失败计数交错写入。
        user = self.session.scalar(select(User).where(User.id == user_id).with_for_update())
        if not user:
            return
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = _utc_naive(now)
        self.session.commit()


class InMemoryAuthRepository:
    """认证接口测试使用的隔离内存仓储。

    它实现与正式仓储相同的协议，但只保存在当前测试进程内，不能用于生产。
    """

    def __init__(self) -> None:
        self._users: dict[int, UserRecord] = {}
        self._accounts: dict[str, int] = {}
        self._sessions: dict[str, tuple[int, datetime, datetime | None]] = {}
        self._next_user_id = 1

    def get_user_by_account(self, account: str) -> UserRecord | None:
        user_id = self._accounts.get(account)
        return self._users.get(user_id) if user_id else None

    def get_user_by_id(self, user_id: int) -> UserRecord | None:
        return self._users.get(user_id)

    def list_users(
        self, *, keyword: str | None, status: UserStatus | None, offset: int, limit: int
    ) -> tuple[list[UserRecord], int]:
        """实现与 SQL 仓储一致的用户筛选，供接口测试使用。"""

        users = list(self._users.values())
        if keyword and (cleaned := keyword.strip().casefold()):
            users = [
                user
                for user in users
                if cleaned in user.account.casefold()
                or cleaned in (user.display_name or "").casefold()
            ]
        if status:
            users = [user for user in users if user.status == status]
        users.sort(key=lambda user: (user.created_at, user.id), reverse=True)
        return users[offset : offset + limit], len(users)

    def set_user_status(self, *, user_id: int, status: UserStatus) -> UserRecord | None:
        user = self._users.get(user_id)
        if user is None:
            return None
        updated = replace(user, status=status)
        self._users[user_id] = updated
        return updated

    def create_user(
        self, *, account: str, password_hash: str, display_name: str | None
    ) -> UserRecord:
        if account in self._accounts:
            raise DuplicateAccountError
        user = UserRecord(
            id=self._next_user_id,
            account=account,
            password_hash=password_hash,
            display_name=display_name,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            campus_verified=False,
            failed_login_attempts=0,
            locked_until=None,
            created_at=datetime.now(UTC),
        )
        self._next_user_id += 1
        self._users[user.id] = user
        self._accounts[user.account] = user.id
        return user

    def create_session(self, *, user_id: int, token_hash: str, expires_at: datetime) -> None:
        self._sessions[token_hash] = (user_id, expires_at, None)

    def get_user_by_active_session(self, *, token_hash: str, now: datetime) -> UserRecord | None:
        session = self._sessions.get(token_hash)
        if not session:
            return None
        user_id, expires_at, revoked_at = session
        if revoked_at is not None or expires_at <= now:
            return None
        return self._users.get(user_id)

    def revoke_session(self, *, token_hash: str, now: datetime) -> bool:
        session = self._sessions.get(token_hash)
        if not session or session[2] is not None:
            return False
        self._sessions[token_hash] = (session[0], session[1], now)
        return True

    def record_login_failure(
        self, *, user_id: int, now: datetime, max_attempts: int, lock_minutes: int
    ) -> None:
        user = self._users.get(user_id)
        if not user:
            return
        attempts = user.failed_login_attempts + 1
        locked_until = user.locked_until
        if attempts >= max_attempts:
            attempts = 0
            locked_until = now + timedelta(minutes=lock_minutes)
        self._users[user_id] = replace(
            user, failed_login_attempts=attempts, locked_until=locked_until
        )

    def record_login_success(self, *, user_id: int, now: datetime) -> None:
        user = self._users.get(user_id)
        if user:
            self._users[user_id] = replace(user, failed_login_attempts=0, locked_until=None)

    def update_user(
        self,
        user_id: int,
        *,
        role: UserRole | None = None,
        status: UserStatus | None = None,
    ) -> None:
        """仅供测试构造管理员或受限账号。"""

        user = self._users[user_id]
        self._users[user_id] = replace(user, role=role or user.role, status=status or user.status)
