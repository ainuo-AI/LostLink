"""HTTP 层的依赖注入工厂。

路由依赖抽象 Repository，而不是自行创建数据库连接，便于测试替换和后续事务扩展。
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.repositories.item_repository import ItemRepository, SqlAlchemyItemRepository


def get_item_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> ItemRepository:
    """用当前请求的 SQLAlchemy Session 创建正式物品仓储。"""

    return SqlAlchemyItemRepository(session)
