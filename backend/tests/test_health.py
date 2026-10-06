"""健康检查接口测试。"""

from fastapi.testclient import TestClient


def test_health_check_returns_service_status(client: TestClient) -> None:
    """服务启动后应返回可识别的状态、环境和请求编号。"""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "LostLink API",
        "version": "0.1.0",
        "environment": "test",
    }
    assert len(response.headers["X-Request-ID"]) == 32
    assert response.headers["Content-Length"] == str(len(response.content))


def test_openapi_document_is_available(client: TestClient) -> None:
    """FastAPI 应生成包含物品列表接口的 OpenAPI 契约。"""

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/items" in response.json()["paths"]
    assert "/api/v1/auth/register" in response.json()["paths"]
    assert "/api/v1/auth/login" in response.json()["paths"]
    assert "/api/v1/auth/logout" in response.json()["paths"]
    assert "/api/v1/users/me" in response.json()["paths"]
    assert "/api/v1/users/me/items" in response.json()["paths"]
    assert "/api/v1/items/{item_id}" in response.json()["paths"]
    assert "/api/v1/items/{item_id}/status" in response.json()["paths"]
