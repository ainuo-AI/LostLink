"""图片、举报、匹配通知和管理后台 API 的端到端契约测试。

测试使用内存仓储覆盖权限、状态转换和模块协作；MySQL 表结构由迁移检查和集成
测试验证，避免快速测试依赖开发者本地数据库。
"""

from fastapi.testclient import TestClient

from app.repositories.auth_repository import InMemoryAuthRepository
from app.schemas.auth import UserRole
from tests.api.test_item_management import authenticated_headers, lost_payload


def found_payload(**overrides: object) -> dict:
    """构造可参与自动匹配的拾物发布请求。"""

    payload = lost_payload(
        type="found",
        title="拾到黑色无线耳机",
        description="黑色充电仓右侧有一道划痕，暂存在值班室等待核验。",
        storage_method="office",
        storage_location="图书馆值班室",
        contact_window="工作日 09:00-17:00",
    )
    payload.update(overrides)
    return payload


def test_upload_associate_and_read_image(client: TestClient) -> None:
    """上传图片后可随物品关联并通过公开地址读取。"""

    headers, _ = authenticated_headers(client)
    uploaded = client.post(
        "/api/v1/uploads/images",
        headers=headers,
        files={"file": ("proof.png", b"\x89PNG\r\n\x1a\nimage-data", "image/png")},
    )
    assert uploaded.status_code == 201
    image = uploaded.json()

    # 临时图片在物品发布前不公开。
    assert client.get(image["url"]).status_code == 404
    created = client.post(
        "/api/v1/items",
        headers=headers,
        json=lost_payload(image_ids=[image["id"]]),
    )
    assert created.status_code == 201
    downloaded = client.get(image["url"])
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"] == "image/png"


def test_report_submission_and_admin_resolution(
    client: TestClient,
    auth_repository: InMemoryAuthRepository,
) -> None:
    """普通用户提交举报后，管理员可处理且审计日志可查询。"""

    user_headers, _ = authenticated_headers(client, "reporter-001")
    report = client.post(
        "/api/v1/items/1/reports",
        headers=user_headers,
        json={"reason": "疑似虚假信息", "description": "地点与描述明显冲突"},
    )
    assert report.status_code == 201
    assert report.json()["status"] == "pending"
    duplicate = client.post(
        "/api/v1/items/1/reports",
        headers=user_headers,
        json={"reason": "重复举报"},
    )
    assert duplicate.status_code == 409

    admin_headers, admin = authenticated_headers(client, "report-admin")
    auth_repository.update_user(admin["id"], role=UserRole.ADMIN)
    resolved = client.patch(
        f"/api/v1/admin/reports/{report.json()['id']}",
        headers=admin_headers,
        json={"status": "resolved", "resolution_note": "已核验并联系发布者修正"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["handled_by_id"] == admin["id"]
    audits = client.get("/api/v1/admin/audit", headers=admin_headers)
    assert audits.status_code == 200
    assert audits.json()["items"][0]["action"] == "report.resolve"


def test_new_opposite_items_generate_match_and_accept_feedback(client: TestClient) -> None:
    """相反类型的新记录会生成双方通知，并允许一次性反馈。"""

    lost_headers, _ = authenticated_headers(client, "lost-owner")
    found_headers, _ = authenticated_headers(client, "found-owner")
    lost = client.post("/api/v1/items", headers=lost_headers, json=lost_payload())
    assert lost.status_code == 201
    found = client.post("/api/v1/items", headers=found_headers, json=found_payload())
    assert found.status_code == 201

    notifications = client.get("/api/v1/notifications", headers=lost_headers)
    assert notifications.status_code == 200
    assert notifications.json()["total"] >= 1
    match = notifications.json()["items"][0]
    assert match["mine"]["id"] == lost.json()["id"]
    assert match["candidate"]["id"] == found.json()["id"]
    assert len(match["dimensions"]) == 5

    feedback = client.patch(
        f"/api/v1/matches/{match['id']}/feedback",
        headers=lost_headers,
        json={"status": "confirmed"},
    )
    assert feedback.status_code == 200
    assert feedback.json()["status"] == "confirmed"
    assert feedback.json()["is_read"] is True
    repeated = client.patch(
        f"/api/v1/matches/{match['id']}/feedback",
        headers=lost_headers,
        json={"status": "rejected", "reason": "特征不符"},
    )
    assert repeated.status_code == 409


def test_admin_user_overview_and_calibration_lifecycle(
    client: TestClient,
    auth_repository: InMemoryAuthRepository,
) -> None:
    """管理员可以限制用户，并完成候选权重版本的审批与启用。"""

    _, target = authenticated_headers(client, "managed-user")
    admin_headers, admin = authenticated_headers(client, "platform-admin")
    auth_repository.update_user(admin["id"], role=UserRole.ADMIN)

    changed = client.patch(
        f"/api/v1/admin/users/{target['id']}/status",
        headers=admin_headers,
        json={"status": "restricted", "reason": "多次发布无关内容"},
    )
    assert changed.status_code == 200
    assert changed.json()["status"] == "restricted"
    overview = client.get("/api/v1/admin/overview", headers=admin_headers)
    assert overview.status_code == 200
    assert overview.json()["users_restricted"] == 1

    task = client.post(
        "/api/v1/admin/calibration/tasks",
        headers=admin_headers,
        json={"category": "数码", "range_start": "2026-09-01", "range_end": "2026-10-01"},
    )
    assert task.status_code == 201
    version_id = task.json()["candidate_version_id"]
    approved = client.patch(
        f"/api/v1/admin/calibration/versions/{version_id}",
        headers=admin_headers,
        json={"action": "approve", "reason": "离线指标达到上线要求"},
    )
    assert approved.status_code == 200
    activated = client.patch(
        f"/api/v1/admin/calibration/versions/{version_id}",
        headers=admin_headers,
        json={"action": "activate", "reason": "批准作为当前匹配权重"},
    )
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"
