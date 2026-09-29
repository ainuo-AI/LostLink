"""SQLAlchemy 声明式模型基类。

所有数据库模型继承同一个 Base，Alembic 才能统一发现表、索引和约束元数据。
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """LostLink 全部持久化模型的共同基类。"""
