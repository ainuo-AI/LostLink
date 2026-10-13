# 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
"""用户资源的 HTTP API 边界。

当前只提供 ``GET /users/me``，用于验证 Bearer 会话并返回安全账号摘要。
管理员用户列表、账号限制和校园认证等未来接口也应在本资源边界中扩展。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_item_service
from app.schemas.auth import UserRead
from app.schemas.item import ItemOwnerListResponse, ItemStatus, RecordType
from app.services.item_service import ItemService, OwnedItemQuery

router = APIRouter(prefix="/users", tags=["users"])


# 文档对应：图2-1 校园用户的有效身份；表1-1 用户与会话。
@router.get("/me", response_model=UserRead, summary="读取当前用户")
def get_me(user: Annotated[UserRead, Depends(get_current_user)]) -> UserRead:
    """返回当前有效会话关联的公开账号摘要。"""

    return user


# 文档对应：图2-2-5 本人记录查询；2.2.5节。
@router.get("/me/items", response_model=ItemOwnerListResponse, summary="查询我的物品记录")
def list_my_items(
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[ItemService, Depends(get_item_service)],
    item_type: Annotated[RecordType | None, Query(alias="type")] = None,
    status: ItemStatus | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ItemOwnerListResponse:
    """按类型和状态分页返回当前用户自己的记录，包括私密管理字段。"""

    return service.list_owned_items(
        OwnedItemQuery(
            item_type=item_type,
            status=status,
            page=page,
            page_size=page_size,
        ),
        user,
    )
