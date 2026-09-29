"""SQLAlchemy 引擎和会话管理。

应用通过短生命周期 Session 访问 MySQL；连接池会在借出连接前检查其可用性。
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    # 异常和 SQL 日志隐藏参数值，避免搜索词等用户输入被意外写入日志。
    hide_parameters=True,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def get_db_session() -> Generator[Session]:
    """为一次请求提供数据库会话，并在请求结束后可靠关闭连接。"""

    with SessionLocal() as session:
        yield session
