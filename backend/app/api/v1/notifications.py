"""匹配通知列表、详情、已读和反馈接口。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_matching_service
from app.schemas.auth import UserRead
from app.schemas.feature import MatchFeedback, MatchNotificationListResponse, MatchNotificationRead
from app.services.feature_service import MatchingService

router = APIRouter(tags=["matching"])


@router.get("/notifications", response_model=MatchNotificationListResponse)
def list_notifications(
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[MatchingService, Depends(get_matching_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> MatchNotificationListResponse:
    """返回当前用户的匹配通知和未读数量。"""

    return service.list(user, page, page_size)


@router.get("/matches/{match_id}", response_model=MatchNotificationRead)
def get_match(
    match_id: int,
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[MatchingService, Depends(get_matching_service)],
) -> MatchNotificationRead:
    """读取属于当前用户的一条匹配详情。"""

    return service.get(match_id, user)


@router.patch("/notifications/{match_id}/read", response_model=MatchNotificationRead)
def mark_notification_read(
    match_id: int,
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[MatchingService, Depends(get_matching_service)],
) -> MatchNotificationRead:
    """只更新通知已读状态，不改变用户反馈结论。"""

    return service.mark_read(match_id, user)


@router.patch("/matches/{match_id}/feedback", response_model=MatchNotificationRead)
def submit_match_feedback(
    match_id: int,
    payload: MatchFeedback,
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[MatchingService, Depends(get_matching_service)],
) -> MatchNotificationRead:
    """拒绝尚未处理的候选匹配，并记录原因。"""

    return service.feedback(match_id, payload, user)
