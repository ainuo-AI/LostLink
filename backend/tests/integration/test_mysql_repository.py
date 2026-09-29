"""SQLAlchemy MySQL Repository 集成测试。

只有设置 TEST_DATABASE_URL 时才运行，避免普通单元测试误连接个人数据库。
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.repositories.item_repository import ItemFilters, SqlAlchemyItemRepository
from app.schemas.item import Campus, ItemStatus, RecordType

test_database_url = os.getenv("TEST_DATABASE_URL")
pytestmark = [
    pytest.mark.mysql,
    pytest.mark.skipif(not test_database_url, reason="TEST_DATABASE_URL is not configured"),
]


def test_mysql_repository_filters_and_counts_seeded_items() -> None:
    """真实 MySQL 应在数据库中完成组合筛选并返回准确总数。"""

    assert test_database_url is not None
    engine = create_engine(test_database_url, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            repository = SqlAlchemyItemRepository(session)
            items, total = repository.list_filtered(
                ItemFilters(
                    keyword="耳机",
                    item_type=RecordType.FOUND,
                    category=None,
                    campus=Campus.NINGHE,
                    area=None,
                    status=ItemStatus.ACTIVE,
                    occurred_after=None,
                    offset=0,
                    limit=20,
                )
            )
    finally:
        engine.dispose()

    assert total == 1
    assert len(items) == 1
    assert items[0].title == "白色无线耳机"
