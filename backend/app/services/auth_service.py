"""注册、登录、会话认证和注销的业务编排层。

``AuthService`` 位于 HTTP API 与 Repository 之间：负责账号规范化、密码验证、
登录失败锁定策略、会话签发和业务错误转换。它只依赖仓储协议和纯安全函数，
不读取 FastAPI Request，也不直接执行 SQL，便于独立测试和以后替换认证入口。
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.errors import AppError
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password_or_dummy,
)
from app.repositories.auth_repository import (
    AuthRepository,
    DuplicateAccountError,
    UserRecord,
)
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead, UserStatus


@dataclass(frozen=True, slots=True)
class AuthPolicy:
    """可配置的会话时长、失败阈值和临时锁定时间。"""

    session_ttl_hours: int = 168
    max_login_attempts: int = 5
    login_lock_minutes: int = 15


class AuthService:
    """编排用户认证流程，不依赖 FastAPI。"""

    def __init__(self, repository: AuthRepository, policy: AuthPolicy | None = None) -> None:
        self.repository = repository
        self.policy = policy or AuthPolicy()

    @staticmethod
    def normalize_account(account: str) -> str:
        """统一去除首尾空白并折叠大小写，避免产生视觉重复账号。"""

        return account.strip().casefold()

    @staticmethod
    def to_user_read(user: UserRecord) -> UserRead:
        """只选择允许对外返回的字段，主动排除密码和登录保护信息。"""

        return UserRead(
            id=user.id,
            account=user.account,
            display_name=user.display_name,
            role=user.role,
            status=user.status,
            campus_verified=user.campus_verified,
            created_at=user.created_at,
        )

    def register(self, payload: RegisterRequest) -> UserRead:
        """创建默认普通、未完成校园验证的账号。"""

        account = self.normalize_account(payload.account)
        if self.repository.get_user_by_account(account):
            raise AppError(code="ACCOUNT_EXISTS", message="该账号已注册", status_code=409)
        try:
            user = self.repository.create_user(
                account=account,
                password_hash=hash_password(payload.password.get_secret_value()),
                display_name=payload.display_name,
            )
        except DuplicateAccountError as exc:
            raise AppError(code="ACCOUNT_EXISTS", message="该账号已注册", status_code=409) from exc
        return self.to_user_read(user)

    def login(
        self,
        payload: LoginRequest,
        *,
        now: datetime | None = None,
    ) -> TokenResponse:
        """验证凭据、应用失败锁定策略并签发服务端会话。"""

        current_time = now or datetime.now(UTC)
        account = self.normalize_account(payload.account)
        user = self.repository.get_user_by_account(account)
        password_matches = verify_password_or_dummy(
            payload.password.get_secret_value(), user.password_hash if user else None
        )

        if not user or not password_matches:
            if user:
                self.repository.record_login_failure(
                    user_id=user.id,
                    now=current_time,
                    max_attempts=self.policy.max_login_attempts,
                    lock_minutes=self.policy.login_lock_minutes,
                )
            raise AppError(
                code="AUTHENTICATION_FAILED",
                message="账号或密码错误",
                status_code=401,
            )

        if user.locked_until and user.locked_until > current_time:
            raise AppError(
                code="AUTHENTICATION_FAILED",
                message="账号或密码错误",
                status_code=401,
            )
        if user.status != UserStatus.ACTIVE:
            raise AppError(code="ACCOUNT_RESTRICTED", message="账号当前不可用", status_code=403)

        token = generate_session_token()
        expires_at = current_time + timedelta(hours=self.policy.session_ttl_hours)
        self.repository.create_session(
            user_id=user.id,
            token_hash=hash_session_token(token),
            expires_at=expires_at,
        )
        self.repository.record_login_success(user_id=user.id, now=current_time)
        return TokenResponse(
            access_token=token,
            expires_in=int((expires_at - current_time).total_seconds()),
            user=self.to_user_read(user),
        )

    def authenticate(self, token: str, *, now: datetime | None = None) -> UserRead:
        """根据未过期且未吊销的令牌加载当前用户。"""

        current_time = now or datetime.now(UTC)
        user = self.repository.get_user_by_active_session(
            token_hash=hash_session_token(token), now=current_time
        )
        if not user:
            raise AppError(code="UNAUTHENTICATED", message="请先登录", status_code=401)
        if user.status != UserStatus.ACTIVE:
            raise AppError(code="ACCOUNT_RESTRICTED", message="账号当前不可用", status_code=403)
        return self.to_user_read(user)

    def logout(self, token: str, *, now: datetime | None = None) -> None:
        """吊销当前会话；无效令牌沿用未认证错误。"""

        current_time = now or datetime.now(UTC)
        revoked = self.repository.revoke_session(
            token_hash=hash_session_token(token), now=current_time
        )
        if not revoked:
            raise AppError(code="UNAUTHENTICATED", message="请先登录", status_code=401)
