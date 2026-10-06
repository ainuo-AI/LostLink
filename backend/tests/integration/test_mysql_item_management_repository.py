"""物品管理 Repository 的可选 MySQL 集成测试。

仅在显式提供已迁移的 ``TEST_DATABASE_URL`` 时运行，验证用户外键、私密字段、
个人列表、编辑、状态事务和审计表能够在真实 MySQL 中协同工作。
"""

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.item import Item
from app.models.item_status_history import ItemStatusHistory
from app.models.user import User
from app.repositories.auth_repository import SqlAlchemyAuthRepository
from app.repositories.item_repository import (
    NewItem,
    OwnedItemFilters,
    SqlAlchemyItemRepository,
)
from app.schemas.item import Campus, CampusArea, ItemStatus, RecordType

test_database_url = os.getenv("TEST_DATABASE_URL")
pytestmark = [
    pytest.mark.mysql,
    pytest.mark.skipif(not test_database_url, reason="TEST_DATABASE_URL is not configured"),
]


def test_mysql_item_management_persists_private_fields_and_status_audit() -> None:
    """正式仓储应在同一数据库中完成完整的记录管理生命周期。"""

    assert test_database_url is not None
    engine = create_engine(test_database_url, pool_pre_ping=True)
    account = f"item-integration-{uuid4().hex}"
    now = datetime.now(UTC)
    item_id: int | None = None
    user_id: int | None = None
    try:
        with Session(engine) as session:
            auth_repository = SqlAlchemyAuthRepository(session)
            item_repository = SqlAlchemyItemRepository(session)
            user = auth_repository.create_user(
                account=account,
                password_hash=hash_password("integration-password"),
                display_name="物品集成测试用户",
            )
            user_id = user.id
            created = item_repository.create(
                NewItem(
                    owner_id=user.id,
                    type=RecordType.LOST,
                    category="数码",
                    title="集成测试耳机",
                    description="只用于隔离数据库的物品管理集成测试。",
                    location="测试楼一层",
                    campus=Campus.DONGLI,
                    area=CampusArea.NORTH,
                    occurred_at=now - timedelta(hours=1),
                    contact_hint="请核验测试特征",
                    contact="13800000000",
                    contact_note="请核验测试特征",
                    storage_method=None,
                    storage_location=None,
                    contact_window=None,
                )
            )
            item_id = created.id

            owned, total = item_repository.list_owned(
                OwnedItemFilters(
                    owner_id=user.id,
                    item_type=RecordType.LOST,
                    status=ItemStatus.ACTIVE,
                    offset=0,
                    limit=20,
                )
            )
            assert total == 1
            assert owned[0].contact == "13800000000"

            edited = item_repository.update_fields(
                created.id,
                {"location": "测试楼二层"},
                expected_status=ItemStatus.ACTIVE,
            )
            assert edited.location == "测试楼二层"

            completed = item_repository.change_status(
                item_id=created.id,
                expected_status=ItemStatus.ACTIVE,
                new_status=ItemStatus.RECOVERED,
                reason="集成测试完成",
                changed_by_id=user.id,
                changed_at=now,
            )
            assert completed.status == ItemStatus.RECOVERED
            history = session.scalar(
                select(ItemStatusHistory).where(ItemStatusHistory.item_id == created.id)
            )
            assert history is not None
            assert history.reason == "集成测试完成"
    finally:
        # 测试只允许使用隔离数据库，并显式清除自己创建的数据。
        if item_id is not None or user_id is not None:
            with Session(engine) as session:
                if item_id is not None:
                    session.execute(delete(Item).where(Item.id == item_id))
                if user_id is not None:
                    session.execute(delete(User).where(User.id == user_id))
                session.commit()
        engine.dispose()
