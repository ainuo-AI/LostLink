"""数据库模型导出入口。

Alembic 导入这个模块后，会加载所有模型并填充 Base.metadata。
"""

from app.models.base import Base
from app.models.feature import (
    AdminAuditLog,
    CalibrationTask,
    CalibrationVersion,
    MatchNotification,
    Report,
    StoredImage,
)
from app.models.item import Item
from app.models.item_status_history import ItemStatusHistory
from app.models.user import AuthSession, User

__all__ = [
    "AdminAuditLog",
    "AuthSession",
    "Base",
    "CalibrationTask",
    "CalibrationVersion",
    "Item",
    "ItemStatusHistory",
    "MatchNotification",
    "Report",
    "StoredImage",
    "User",
]
