"""认证 API 与通用权限守卫的快速测试。

测试通过内存仓储覆盖公开接口行为，不连接 MySQL；正式仓储的最小读写与吊销
流程由 ``tests/integration/test_mysql_auth_repository.py`` 在隔离数据库中验证。
"""

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.core.errors import AppError
from app.core.security import require_admin_role, require_owner_or_admin
from app.repositories.auth_repository import InMemoryAuthRepository
from app.schemas.auth import UserRead, UserRole, UserStatus


def register(client: TestClient, account: str = "20260001") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"account": account, "password": "safe-password-123", "display_name": "测试用户"},
    )
    assert response.status_code == 201
    return response.json()


def login(client: TestClient, account: str = "20260001") -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={"account": account, "password": "safe-password-123"},
    )
    assert response.status_code == 200
    return response.json()


def test_register_creates_unverified_regular_user_without_exposing_password(
    client: TestClient,
    auth_repository: InMemoryAuthRepository,
) -> None:
    body = register(client, "Student.001")

    assert body["account"] == "student.001"
    assert body["display_name"] == "测试用户"
    assert body["role"] == "user"
    assert body["status"] == "active"
    assert body["campus_verified"] is False
    assert "password" not in str(body)
    stored = auth_repository.get_user_by_account("student.001")
    assert stored is not None
    assert stored.password_hash != "safe-password-123"
    assert stored.password_hash.startswith("scrypt$")


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"account": "20260001", "password": "short"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_register_rejects_duplicate_account_case_insensitively(client: TestClient) -> None:
    register(client, "Student.001")

    response = client.post(
        "/api/v1/auth/register",
        json={"account": "STUDENT.001", "password": "another-password"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ACCOUNT_EXISTS"


def test_login_and_current_user_complete_session_flow(client: TestClient) -> None:
    registered = register(client)
    authenticated = login(client)

    assert authenticated["token_type"] == "bearer"
    assert authenticated["expires_in"] == 168 * 60 * 60
    assert authenticated["user"]["id"] == registered["id"]
    token = authenticated["access_token"]

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["account"] == "20260001"


def test_login_returns_same_safe_error_for_unknown_account_and_wrong_password(
    client: TestClient,
) -> None:
    register(client)

    wrong_password = client.post(
        "/api/v1/auth/login",
        json={"account": "20260001", "password": "wrong-password"},
    )
    unknown_account = client.post(
        "/api/v1/auth/login",
        json={"account": "20269999", "password": "wrong-password"},
    )

    assert wrong_password.status_code == unknown_account.status_code == 401
    assert wrong_password.json()["code"] == unknown_account.json()["code"]
    assert wrong_password.json()["message"] == unknown_account.json()["message"]


def test_repeated_login_failures_temporarily_lock_account(client: TestClient) -> None:
    register(client)
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={"account": "20260001", "password": "wrong-password"},
        )
        assert response.status_code == 401

    correct_password = client.post(
        "/api/v1/auth/login",
        json={"account": "20260001", "password": "safe-password-123"},
    )
    assert correct_password.status_code == 401
    assert correct_password.json()["code"] == "AUTHENTICATION_FAILED"


def test_logout_revokes_only_the_current_session(client: TestClient) -> None:
    register(client)
    first = login(client)["access_token"]
    second = login(client)["access_token"]

    response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {first}"})
    assert response.status_code == 204
    assert response.content == b""

    revoked = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {first}"})
    still_active = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {second}"})
    assert revoked.status_code == 401
    assert still_active.status_code == 200


def test_protected_endpoint_requires_bearer_token(client: TestClient) -> None:
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHENTICATED"


def test_restricted_user_cannot_continue_using_existing_session(
    client: TestClient,
    auth_repository: InMemoryAuthRepository,
) -> None:
    user = register(client)
    token = login(client)["access_token"]
    auth_repository.update_user(user["id"], status=UserStatus.RESTRICTED)

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_RESTRICTED"


@dataclass
class Resource:
    owner_id: int | None


def build_user(*, user_id: int = 1, role: UserRole = UserRole.USER) -> UserRead:
    return UserRead(
        id=user_id,
        account=f"user-{user_id}",
        display_name=None,
        role=role,
        status=UserStatus.ACTIVE,
        campus_verified=False,
        created_at="2026-10-05T00:00:00Z",
    )


def test_owner_or_admin_permission_guard() -> None:
    require_owner_or_admin(build_user(user_id=1), Resource(owner_id=1))
    require_owner_or_admin(build_user(role=UserRole.ADMIN), Resource(owner_id=99))

    with pytest.raises(AppError) as forbidden:
        require_owner_or_admin(build_user(user_id=2), Resource(owner_id=1))
    assert forbidden.value.code == "FORBIDDEN"


def test_admin_permission_guard() -> None:
    assert require_admin_role(build_user(role=UserRole.ADMIN)).role == UserRole.ADMIN

    with pytest.raises(AppError) as forbidden:
        require_admin_role(build_user())
    assert forbidden.value.code == "FORBIDDEN"
