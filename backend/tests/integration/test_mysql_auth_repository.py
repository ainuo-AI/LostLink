"""认证 Repository 的可选 MySQL 集成测试。

仅在显式提供 ``TEST_DATABASE_URL`` 时运行，用于验证真实 SQLAlchemy/MySQL
用户写入、会话查询和吊销行为；默认测试不会连接或修改个人数据库。
"""

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from app.core.security import hash_password, hash_session_token
from app.models.user import User
from app.repositories.auth_repository import SqlAlchemyAuthRepository

test_database_url = os.getenv("TEST_DATABASE_URL")
pytestmark = [
    pytest.mark.mysql,
    pytest.mark.skipif(not test_database_url, reason="TEST_DATABASE_URL is not configured"),
]


def test_mysql_auth_repository_persists_and_revokes_session() -> None:
    """正式仓储应能创建用户、认证会话并立即吊销。"""

    assert test_database_url is not None
    account = f"integration-{uuid4().hex}"
    token_hash = hash_session_token(uuid4().hex)
    now = datetime.now(UTC)
    engine = create_engine(test_database_url, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            repository = SqlAlchemyAuthRepository(session)
            user = repository.create_user(
                account=account,
                password_hash=hash_password("integration-password"),
                display_name="集成测试用户",
            )
            repository.create_session(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=now + timedelta(minutes=5),
            )

            authenticated = repository.get_user_by_active_session(token_hash=token_hash, now=now)
            assert authenticated is not None
            assert authenticated.account == account

            assert repository.revoke_session(token_hash=token_hash, now=now) is True
            assert repository.get_user_by_active_session(token_hash=token_hash, now=now) is None

            session.execute(delete(User).where(User.id == user.id))
            session.commit()
    finally:
        engine.dispose()
