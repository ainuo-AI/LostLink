"""数据库模型导出入口。

Alembic 导入这个模块后，会加载所有模型并填充 Base.metadata。
"""

from app.models.base import Base
from app.models.item import Item

__all__ = ["Base", "Item"]
