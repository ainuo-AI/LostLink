"""物品列表接口集成测试。"""

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.dependencies import get_item_repository
from app.repositories.item_repository import ItemFilters


def test_list_items_hides_closed_records_by_default(client: TestClient) -> None:
    """默认查询只返回进行中的记录，并按时间倒序排列。"""

    response = client.get("/api/v1/items")
    body = response.json()

    assert response.status_code == 200
    assert body["total"] == 6
    assert all(item["status"] == "active" for item in body["items"])
    assert [item["id"] for item in body["items"]] == [1, 2, 3, 4, 5, 6]


def test_list_items_supports_combined_filters(client: TestClient) -> None:
    """关键词、类型和校区可以组合使用。"""

    response = client.get(
        "/api/v1/items",
        params={"keyword": "耳机", "type": "found", "campus": "宁河校区"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["total"] == 1
    assert body["items"][0]["title"] == "白色无线耳机"


def test_list_items_supports_stable_pagination(client: TestClient) -> None:
    """分页应返回正确切片，同时保留总记录数。"""

    response = client.get("/api/v1/items", params={"page": 2, "page_size": 2})
    body = response.json()

    assert response.status_code == 200
    assert body["page"] == 2
    assert body["page_size"] == 2
    assert body["total"] == 6
    assert [item["id"] for item in body["items"]] == [3, 4]


def test_list_items_can_explicitly_query_closed_records(client: TestClient) -> None:
    """显式指定 closed 状态时可以查询历史关闭记录。"""

    response = client.get("/api/v1/items", params={"status": "closed"})
    body = response.json()

    assert response.status_code == 200
    assert body["total"] == 1
    assert body["items"][0]["id"] == 7


def test_list_items_returns_standard_validation_error(client: TestClient) -> None:
    """非法分页参数应返回项目统一错误结构。"""

    response = client.get("/api/v1/items", params={"page": 0})
    body = response.json()

    assert response.status_code == 422
    assert body["code"] == "VALIDATION_ERROR"
    assert body["message"] == "请求参数不正确"
    assert body["details"][0]["field"] == "query.page"
    assert body["request_id"] == response.headers["X-Request-ID"]


def test_list_items_returns_safe_error_when_database_is_unavailable(
    client: TestClient,
) -> None:
    """数据库异常应转换为 503，且响应中不暴露 SQL 或连接信息。"""

    class UnavailableRepository:
        """模拟无法访问 MySQL 的 Repository。"""

        def list_filtered(self, filters: ItemFilters) -> tuple[list, int]:
            raise OperationalError("SELECT secret", {"password": "secret"}, Exception("down"))

    client.app.dependency_overrides[get_item_repository] = UnavailableRepository
    response = client.get("/api/v1/items")
    body = response.json()

    assert response.status_code == 503
    assert body["code"] == "DATABASE_UNAVAILABLE"
    assert body["message"] == "数据服务暂时不可用，请稍后重试"
    assert "secret" not in response.text
    assert body["request_id"] == response.headers["X-Request-ID"]
