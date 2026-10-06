"""物品发布、详情、个人列表、编辑和状态闭环 API 测试。

测试使用内存用户与物品仓储，重点验证 HTTP 契约、敏感字段边界、资源归属、
状态转换及审计行为；真实 MySQL 写入由可选集成测试覆盖。
"""

from fastapi.testclient import TestClient

from app.repositories.auth_repository import InMemoryAuthRepository
from app.repositories.item_repository import InMemoryItemRepository
from app.schemas.auth import UserRole


def authenticated_headers(
    client: TestClient,
    account: str = "20260001",
) -> tuple[dict[str, str], dict]:
    """注册并登录一个测试用户，返回认证头和用户摘要。"""

    registered = client.post(
        "/api/v1/auth/register",
        json={"account": account, "password": "safe-password-123"},
    )
    assert registered.status_code == 201
    logged_in = client.post(
        "/api/v1/auth/login",
        json={"account": account, "password": "safe-password-123"},
    )
    assert logged_in.status_code == 200
    body = logged_in.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, registered.json()


def lost_payload(**overrides: object) -> dict:
    """构造符合前端字段的失物发布请求。"""

    payload: dict[str, object] = {
        "type": "lost",
        "category": "数码",
        "title": "黑色无线耳机",
        "description": "黑色充电仓，外壳右侧有一道明显划痕。",
        "location": "图书馆二层",
        "campus": "东丽校区",
        "area": "北区",
        "occurred_at": "2026-10-01T08:00:00Z",
        "contact": "13800000000",
        "contact_note": "请先描述耳机保护套特征",
        "image_ids": [],
    }
    payload.update(overrides)
    return payload


def test_public_detail_replaces_list_scan_without_exposing_private_contact(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/items/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert "contact" not in response.json()
    assert "owner_id" not in response.json()


def test_create_requires_login_and_rejects_client_owner_id(client: TestClient) -> None:
    unauthenticated = client.post("/api/v1/items", json=lost_payload())
    assert unauthenticated.status_code == 401

    headers, _ = authenticated_headers(client)
    forged = client.post(
        "/api/v1/items",
        headers=headers,
        json=lost_payload(owner_id=999),
    )
    assert forged.status_code == 422


def test_create_and_list_my_items_keep_contact_private(client: TestClient) -> None:
    headers, user = authenticated_headers(client)
    created = client.post("/api/v1/items", headers=headers, json=lost_payload())

    assert created.status_code == 201
    owner_body = created.json()
    assert owner_body["owner_id"] == user["id"]
    assert owner_body["contact"] == "13800000000"
    assert owner_body["status"] == "active"

    public = client.get(f"/api/v1/items/{owner_body['id']}")
    assert public.status_code == 200
    assert "contact" not in public.json()
    assert public.json()["contact_hint"] == "请先描述耳机保护套特征"

    mine = client.get(
        "/api/v1/users/me/items",
        headers=headers,
        params={"type": "lost", "status": "active"},
    )
    assert mine.status_code == 200
    assert mine.json()["total"] == 1
    assert mine.json()["items"][0]["contact"] == "13800000000"


def test_found_item_requires_complete_storage_information(client: TestClient) -> None:
    headers, _ = authenticated_headers(client)
    response = client.post(
        "/api/v1/items",
        headers=headers,
        json=lost_payload(type="found"),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_create_rejects_unknown_image_identifiers(
    client: TestClient,
) -> None:
    headers, _ = authenticated_headers(client)
    response = client.post(
        "/api/v1/items",
        headers=headers,
        json=lost_payload(image_ids=["demo-image-local-only"]),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "IMAGE_NOT_AVAILABLE"


def test_create_rejects_future_occurred_time(client: TestClient) -> None:
    headers, _ = authenticated_headers(client)
    response = client.post(
        "/api/v1/items",
        headers=headers,
        json=lost_payload(occurred_at="2099-01-01T00:00:00Z"),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "ITEM_VALIDATION_ERROR"


def test_only_owner_or_admin_can_edit_record(
    client: TestClient,
    auth_repository: InMemoryAuthRepository,
) -> None:
    owner_headers, _ = authenticated_headers(client, "owner-001")
    created = client.post("/api/v1/items", headers=owner_headers, json=lost_payload()).json()

    other_headers, _ = authenticated_headers(client, "other-001")
    forbidden = client.patch(
        f"/api/v1/items/{created['id']}",
        headers=other_headers,
        json={"title": "不应成功的修改"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "FORBIDDEN"

    admin_headers, admin = authenticated_headers(client, "admin-001")
    auth_repository.update_user(admin["id"], role=UserRole.ADMIN)
    updated = client.patch(
        f"/api/v1/items/{created['id']}",
        headers=admin_headers,
        json={"title": "管理员核对后的标题"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "管理员核对后的标题"


def test_owner_can_edit_and_complete_lost_item_with_audit(
    client: TestClient,
    item_repository: InMemoryItemRepository,
) -> None:
    headers, user = authenticated_headers(client)
    created = client.post("/api/v1/items", headers=headers, json=lost_payload()).json()

    edited = client.patch(
        f"/api/v1/items/{created['id']}",
        headers=headers,
        json={
            "location": "图书馆三层",
            "contact": "owner@example.com",
            "contact_note": None,
        },
    )
    assert edited.status_code == 200
    assert edited.json()["location"] == "图书馆三层"
    assert edited.json()["contact"] == "owner@example.com"
    assert edited.json()["contact_hint"] == "联系方式已保护，请先核验物品特征。"

    completed = client.patch(
        f"/api/v1/items/{created['id']}/status",
        headers=headers,
        json={"status": "recovered", "reason": "已在图书馆服务台找回"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "recovered"
    assert completed.json()["closure_reason"] == "已在图书馆服务台找回"
    assert completed.json()["closed_at"] is not None
    assert item_repository.status_history == [
        (created["id"], "active", "recovered", user["id"], "已在图书馆服务台找回")
    ]

    public_detail = client.get(f"/api/v1/items/{created['id']}")
    assert public_detail.status_code == 200
    assert public_detail.json()["status"] == "recovered"
    assert "contact" not in public_detail.json()

    # 默认首页列表仍只展示 active，终态记录不会重新出现。
    public_list = client.get("/api/v1/items")
    assert all(item["id"] != created["id"] for item in public_list.json()["items"])
    mine = client.get(
        "/api/v1/users/me/items",
        headers=headers,
        params={"status": "recovered"},
    )
    assert mine.status_code == 200
    assert mine.json()["total"] == 1

    edit_finished = client.patch(
        f"/api/v1/items/{created['id']}",
        headers=headers,
        json={"title": "终态后不允许修改"},
    )
    assert edit_finished.status_code == 409
    assert edit_finished.json()["code"] == "ITEM_NOT_EDITABLE"


def test_status_transition_must_match_record_type(client: TestClient) -> None:
    headers, _ = authenticated_headers(client)
    created = client.post("/api/v1/items", headers=headers, json=lost_payload()).json()

    response = client.patch(
        f"/api/v1/items/{created['id']}/status",
        headers=headers,
        json={"status": "returned"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATUS_TRANSITION"


def test_found_item_can_be_marked_returned(client: TestClient) -> None:
    headers, _ = authenticated_headers(client)
    created = client.post(
        "/api/v1/items",
        headers=headers,
        json=lost_payload(
            type="found",
            storage_method="office",
            storage_location="教学楼值班室",
            contact_window="工作日 09:00-17:00",
        ),
    )
    assert created.status_code == 201

    returned = client.patch(
        f"/api/v1/items/{created.json()['id']}/status",
        headers=headers,
        json={"status": "returned", "reason": "已交还失主"},
    )
    assert returned.status_code == 200
    assert returned.json()["status"] == "returned"
