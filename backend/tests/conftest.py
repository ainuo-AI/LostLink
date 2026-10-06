"""pytest 公共测试夹具。"""

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_auth_repository, get_feature_repository, get_item_repository
from app.core.config import Settings
from app.main import create_app
from app.repositories.auth_repository import InMemoryAuthRepository
from app.repositories.feature_repository import InMemoryFeatureRepository
from app.repositories.item_repository import InMemoryItemRepository
from tests.factories import build_demo_items


@pytest.fixture
def auth_repository() -> InMemoryAuthRepository:
    """为每个测试提供隔离的认证数据。"""

    return InMemoryAuthRepository()


@pytest.fixture
def item_repository() -> InMemoryItemRepository:
    """提供同时支持查询和写入的隔离物品仓储。"""

    return InMemoryItemRepository(build_demo_items())


@pytest.fixture
def feature_repository() -> InMemoryFeatureRepository:
    """为图片、举报、匹配与管理功能提供隔离内存仓储。"""

    return InMemoryFeatureRepository()


@pytest.fixture
def client(
    auth_repository: InMemoryAuthRepository,
    item_repository: InMemoryItemRepository,
    feature_repository: InMemoryFeatureRepository,
    tmp_path,
) -> TestClient:
    """为每个测试创建配置固定的 API 客户端。"""

    settings = Settings(
        app_env="test",
        cors_origins=["http://testserver"],
        upload_directory=tmp_path / "uploads",
    )
    application = create_app(settings)

    # 快速接口测试使用内存仓储，数据库行为由单独的 MySQL 集成测试验证。
    application.dependency_overrides[get_item_repository] = lambda: item_repository
    application.dependency_overrides[get_auth_repository] = lambda: auth_repository
    application.dependency_overrides[get_feature_repository] = lambda: feature_repository

    with TestClient(application) as test_client:
        yield test_client
