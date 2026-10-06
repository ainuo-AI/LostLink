"""HTTP 层的依赖注入和认证守卫。

路由依赖抽象 Repository，而不是自行创建数据库连接，便于测试替换和后续事务扩展。
认证相关依赖在这里统一组装 Repository、策略和 Service，并把 Bearer 令牌转换为
当前用户；业务路由不需要重复解析请求头或检查账号状态。
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.core.errors import AppError
from app.core.security import require_admin_role
from app.repositories.auth_repository import AuthRepository, SqlAlchemyAuthRepository
from app.repositories.feature_repository import FeatureRepository, SqlAlchemyFeatureRepository
from app.repositories.item_repository import ItemRepository, SqlAlchemyItemRepository
from app.schemas.auth import UserRead
from app.services.auth_service import AuthPolicy, AuthService
from app.services.feature_service import AdminService, MatchingService, MediaService, ReportService
from app.services.item_service import ItemService

bearer_scheme = HTTPBearer(auto_error=False)


def get_item_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> ItemRepository:
    """用当前请求的 SQLAlchemy Session 创建正式物品仓储。"""

    return SqlAlchemyItemRepository(session)


def get_feature_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> FeatureRepository:
    """用同一个请求数据库会话创建新增功能仓储。"""

    return SqlAlchemyFeatureRepository(session)


def get_item_service(
    repository: Annotated[ItemRepository, Depends(get_item_repository)],
    features: Annotated[FeatureRepository, Depends(get_feature_repository)],
) -> ItemService:
    """组装物品查询与管理 Service，便于测试替换同一个 Repository。"""

    return ItemService(repository, features)


# 以下依赖组成认证链：数据库会话 → Repository → Service → Bearer 用户。
def get_auth_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> AuthRepository:
    """用当前请求的数据库会话创建认证仓储。"""

    return SqlAlchemyAuthRepository(session)


def get_auth_service(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    """根据应用配置组装认证策略。"""

    policy = AuthPolicy(
        session_ttl_hours=settings.auth_session_ttl_hours,
        max_login_attempts=settings.auth_max_login_attempts,
        login_lock_minutes=settings.auth_login_lock_minutes,
    )
    return AuthService(repository, policy)


def get_media_service(
    repository: Annotated[FeatureRepository, Depends(get_feature_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MediaService:
    """组装带上传目录和大小限制的图片 Service。"""

    return MediaService(repository, settings.upload_directory, settings.upload_max_bytes)


def get_report_service(
    features: Annotated[FeatureRepository, Depends(get_feature_repository)],
    items: Annotated[ItemRepository, Depends(get_item_repository)],
) -> ReportService:
    """组装举报 Service。"""

    return ReportService(features, items)


def get_matching_service(
    features: Annotated[FeatureRepository, Depends(get_feature_repository)],
    items: Annotated[ItemRepository, Depends(get_item_repository)],
) -> MatchingService:
    """组装匹配通知 Service。"""

    return MatchingService(features, items)


def get_admin_service(
    auth: Annotated[AuthRepository, Depends(get_auth_repository)],
    items: Annotated[ItemRepository, Depends(get_item_repository)],
    features: Annotated[FeatureRepository, Depends(get_feature_repository)],
) -> AdminService:
    """组装管理端用户、审计和校准 Service。"""

    return AdminService(auth, items, features)


def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    """提取 Bearer 令牌并统一处理缺失或错误认证方案。"""

    if not credentials or credentials.scheme.lower() != "bearer":
        raise AppError(code="UNAUTHENTICATED", message="请先登录", status_code=401)
    return credentials.credentials


def get_current_user(
    token: Annotated[str, Depends(get_bearer_token)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserRead:
    """加载当前已登录且状态正常的用户。"""

    return service.authenticate(token)


def require_admin(
    user: Annotated[UserRead, Depends(get_current_user)],
) -> UserRead:
    """供管理端路由复用的角色权限依赖。"""

    return require_admin_role(user)
