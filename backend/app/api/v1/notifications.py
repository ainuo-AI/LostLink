# 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
# 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
"""匹配通知列表、详情、已读和反馈接口。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_matching_service
from app.schemas.auth import UserRead
from app.schemas.feature import MatchFeedback, MatchNotificationListResponse, MatchNotificationRead
from app.services.feature_service import MatchingService

router = APIRouter(tags=["matching"])


# 文档对应：图2-2-6 通知列表请求；2.2.6、2.2.7节。
# 设计文档对应：图3-2-5 读取本人通知列表。
@router.get("/notifications", response_model=MatchNotificationListResponse)
def list_notifications(
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[MatchingService, Depends(get_matching_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> MatchNotificationListResponse:
    """返回当前用户的匹配通知和未读数量。"""

    return service.list(user, page, page_size)


# 文档对应：图2-2-6、图2-2-7 的候选详情请求；2.2.6、2.2.7节。
# 设计文档对应：图3-2-6 读取本人候选详情。
@router.get("/matches/{match_id}", response_model=MatchNotificationRead)
def get_match(
    match_id: int,
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[MatchingService, Depends(get_matching_service)],
) -> MatchNotificationRead:
    """读取属于当前用户的一条匹配详情。"""

    return service.get(match_id, user)


# 文档对应：图2-2-6 标记通知已读请求；2.2.6、2.2.7节。
# 设计文档对应：图3-2-5、图3-2-6 标记单条通知已读。
@router.patch("/notifications/{match_id}/read", response_model=MatchNotificationRead)
def mark_notification_read(
    match_id: int,
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[MatchingService, Depends(get_matching_service)],
) -> MatchNotificationRead:
    """只更新通知已读状态，不改变用户反馈结论。"""

    return service.mark_read(match_id, user)


# 文档对应：图2-2-7 确认或拒绝请求；2.2.6、2.2.7节。
# 设计文档对应：图4-1-8 转发接收者确认或拒绝候选的请求。
@router.patch("/matches/{match_id}/feedback", response_model=MatchNotificationRead)
def submit_match_feedback(
    match_id: int,
    payload: MatchFeedback,
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[MatchingService, Depends(get_matching_service)],
) -> MatchNotificationRead:
    """确认或拒绝尚未处理的候选匹配。"""

    return service.feedback(match_id, payload, user)
