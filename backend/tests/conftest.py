"""pytest 公共测试夹具。"""

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_item_repository
from app.core.config import Settings
from app.main import create_app
from app.repositories.item_repository import InMemoryItemRepository
from tests.factories import build_demo_items


@pytest.fixture
def client() -> TestClient:
    """为每个测试创建配置固定的 API 客户端。"""

    settings = Settings(app_env="test", cors_origins=["http://testserver"])
    application = create_app(settings)

    # 快速接口测试使用内存仓储，数据库行为由单独的 MySQL 集成测试验证。
    repository = InMemoryItemRepository(build_demo_items())
    application.dependency_overrides[get_item_repository] = lambda: repository

    with TestClient(application) as test_client:
        yield test_client
