"""认证使用的纯安全工具和通用授权规则。

本模块集中处理密码的 scrypt 哈希与恒定时间比较、随机会话令牌生成、
令牌摘要计算，以及“有效用户 / 管理员 / 资源所有者”权限判断。函数不访问
数据库，也不依赖 FastAPI，因此可以被 Service、API 依赖和单元测试共同复用。

账号查询、失败次数和会话吊销等持久化操作不在这里完成，避免安全算法与
具体数据库实现耦合。
"""

import base64
import hashlib
import hmac
import secrets
from typing import Protocol

from app.core.errors import AppError
from app.schemas.auth import UserRead, UserRole, UserStatus

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
DERIVED_KEY_BYTES = 32


def _derive_password(password: str, salt: bytes, *, n: int, r: int, p: int) -> bytes:
    """使用内存困难的 scrypt 算法派生不可逆密码摘要。"""

    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=DERIVED_KEY_BYTES,
    )


def hash_password(password: str) -> str:
    """生成包含算法参数和随机盐的可持久化密码摘要。"""

    salt = secrets.token_bytes(SALT_BYTES)
    derived = _derive_password(password, salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return "$".join(
        (
            "scrypt",
            str(SCRYPT_N),
            str(SCRYPT_R),
            str(SCRYPT_P),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(derived).decode("ascii"),
        )
    )


def verify_password(password: str, encoded: str) -> bool:
    """验证密码；损坏或未知格式一律按不匹配处理。"""

    try:
        algorithm, n_text, r_text, p_text, salt_text, expected_text = encoded.split("$")
        if algorithm != "scrypt":
            return False
        n, r, p = int(n_text), int(r_text), int(p_text)
        if n != SCRYPT_N or r != SCRYPT_R or p != SCRYPT_P:
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(expected_text.encode("ascii"))
        actual = _derive_password(password, salt, n=n, r=r, p=p)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


# 未知账号也执行一次真实哈希验证，降低通过响应耗时枚举账号的风险。
_DUMMY_PASSWORD_HASH = hash_password("lostlink-dummy-password")


def verify_password_or_dummy(password: str, encoded: str | None) -> bool:
    """账号不存在时使用固定哑摘要执行等价计算。"""

    return verify_password(password, encoded or _DUMMY_PASSWORD_HASH)


def generate_session_token() -> str:
    """生成具有足够熵、适合 Bearer 认证的随机令牌。"""

    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """数据库只保存令牌摘要，数据库泄露时不直接暴露有效会话。"""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def require_active_user(user: UserRead) -> UserRead:
    """拒绝受限账号执行任何受保护操作。"""

    if user.status != UserStatus.ACTIVE:
        raise AppError(code="ACCOUNT_RESTRICTED", message="账号当前不可用", status_code=403)
    return user


def require_admin_role(user: UserRead) -> UserRead:
    """要求当前用户具有管理员角色。"""

    require_active_user(user)
    if user.role != UserRole.ADMIN:
        raise AppError(code="FORBIDDEN", message="没有执行此操作的权限", status_code=403)
    return user


class OwnedResource(Protocol):
    """资源归属检查需要的最小结构。

    后续物品、举报等模型只要公开 ``owner_id``，无需继承共同基类即可复用
    ``require_owner_or_admin``。
    """

    owner_id: int | None


def require_owner_or_admin(user: UserRead, resource: OwnedResource) -> None:
    """仅允许资源所有者或管理员继续执行修改。"""

    require_active_user(user)
    if user.role != UserRole.ADMIN and resource.owner_id != user.id:
        raise AppError(code="FORBIDDEN", message="没有执行此操作的权限", status_code=403)
