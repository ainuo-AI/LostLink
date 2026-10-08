"""图片、举报、匹配通知与管理后台的业务编排。

各 Service 在这里执行文件校验、资源归属、状态转换和管理员审计。API 层只负责
参数绑定；Repository 只负责持久化，因此权限规则不会散落到路由或数据库模型中。
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.core.errors import AppError
from app.integrations.multimodal_matching import MultimodalMatcher
from app.repositories.auth_repository import AuthRepository, UserRecord
from app.repositories.feature_repository import (
    AuditRecord,
    CalibrationTaskRecord,
    CalibrationVersionRecord,
    FeatureRepository,
    ImageRecord,
    MatchRecord,
    ReportRecord,
)
from app.repositories.item_repository import ConcurrentItemUpdateError, ItemRecord, ItemRepository
from app.schemas.auth import UserRead, UserRole, UserStatus
from app.schemas.feature import (
    AdminUserListResponse,
    AuditLogListResponse,
    AuditLogRead,
    CalibrationTaskCreate,
    CalibrationTaskRead,
    CalibrationVersionAction,
    CalibrationVersionRead,
    ImageRead,
    MatchDimension,
    MatchFeedback,
    MatchNotificationListResponse,
    MatchNotificationRead,
    MatchStatus,
    OverviewRead,
    ReportCreate,
    ReportListResponse,
    ReportRead,
    ReportResolve,
    ReportStatus,
    UserStatusUpdate,
)
from app.schemas.item import ItemRead, ItemStatus
from app.services.campus_distance import campus_distance_table


class MediaService:
    """校验图片内容、管理受控文件路径并维护物品关联。"""

    _signatures = {
        "image/jpeg": (b"\xff\xd8\xff",),
        "image/png": (b"\x89PNG\r\n\x1a\n",),
        "image/webp": (b"RIFF",),
    }
    _extensions = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}

    def __init__(
        self, repository: FeatureRepository, upload_directory: Path, max_bytes: int
    ) -> None:
        self.repository = repository
        self.upload_directory = upload_directory.resolve()
        self.max_bytes = max_bytes

    def upload(
        self, *, data: bytes, content_type: str, original_name: str, user: UserRead
    ) -> ImageRead:
        """验证 MIME、文件签名和大小后，以不可预测名称落盘。"""

        if not data or len(data) > self.max_bytes:
            raise AppError(
                code="IMAGE_SIZE_INVALID", message="图片不能为空且不能超过 5MB", status_code=422
            )
        signatures = self._signatures.get(content_type)
        valid = signatures and any(data.startswith(signature) for signature in signatures)
        if content_type == "image/webp":
            valid = bool(valid and len(data) >= 12 and data[8:12] == b"WEBP")
        if not valid:
            raise AppError(
                code="IMAGE_TYPE_INVALID",
                message="仅支持有效的 JPG、PNG 或 WebP 图片",
                status_code=422,
            )

        image_id = str(uuid4())
        storage_key = f"{image_id}{self._extensions[content_type]}"
        self.upload_directory.mkdir(parents=True, exist_ok=True)
        path = self.upload_directory / storage_key
        path.write_bytes(data)
        try:
            record = self.repository.create_image(
                ImageRecord(
                    id=image_id,
                    owner_id=user.id,
                    item_id=None,
                    original_name=Path(original_name).name[:255] or storage_key,
                    content_type=content_type,
                    size_bytes=len(data),
                    sha256=hashlib.sha256(data).hexdigest(),
                    storage_key=storage_key,
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return self._read(record)

    def locate(self, image_id: str) -> tuple[Path, str]:
        """仅允许公开读取已关联到物品的图片。"""

        record = self.repository.get_image(image_id)
        if record is None or record.item_id is None:
            raise AppError(code="IMAGE_NOT_FOUND", message="未找到该图片", status_code=404)
        path = (self.upload_directory / record.storage_key).resolve()
        if self.upload_directory not in path.parents or not path.is_file():
            raise AppError(code="IMAGE_NOT_FOUND", message="图片文件不存在", status_code=404)
        return path, record.content_type

    def delete(self, image_id: str, user: UserRead) -> None:
        """只允许上传者删除尚未关联到物品的图片。"""

        record = self.repository.get_image(image_id)
        if record is None or record.owner_id != user.id:
            raise AppError(code="IMAGE_NOT_FOUND", message="未找到该图片", status_code=404)
        if record.item_id is not None:
            raise AppError(
                code="IMAGE_IN_USE", message="已关联物品的图片不能直接删除", status_code=409
            )
        self.repository.delete_image(image_id)
        (self.upload_directory / record.storage_key).unlink(missing_ok=True)

    @staticmethod
    def _read(record: ImageRecord) -> ImageRead:
        return ImageRead(
            id=record.id,
            content_type=record.content_type,
            size_bytes=record.size_bytes,
            url=f"/api/v1/uploads/images/{record.id}",
            created_at=record.created_at,
        )


class ReportService:
    """处理举报提交、个人查询和管理员结案。"""

    def __init__(self, features: FeatureRepository, items: ItemRepository) -> None:
        self.features = features
        self.items = items

    def create(self, item_id: int, payload: ReportCreate, user: UserRead) -> ReportRead:
        item = self.items.get_by_id(item_id)
        if item is None:
            raise AppError(code="ITEM_NOT_FOUND", message="未找到该物品记录", status_code=404)
        if item.owner_id == user.id:
            raise AppError(
                code="SELF_REPORT_FORBIDDEN", message="不能举报自己发布的记录", status_code=409
            )
        if self.features.has_pending_report(item_id=item_id, reporter_id=user.id):
            raise AppError(
                code="REPORT_ALREADY_PENDING",
                message="你已经举报过该记录，请等待处理",
                status_code=409,
            )
        return self._read(
            self.features.create_report(
                item_id=item_id,
                reporter_id=user.id,
                reason=payload.reason,
                description=payload.description,
            )
        )

    def list_mine(self, user: UserRead, page: int, page_size: int) -> ReportListResponse:
        rows, total = self.features.list_reports(
            reporter_id=user.id, status=None, offset=(page - 1) * page_size, limit=page_size
        )
        return ReportListResponse(
            items=[self._read(row) for row in rows], page=page, page_size=page_size, total=total
        )

    def list_admin(
        self, status: ReportStatus | None, page: int, page_size: int
    ) -> ReportListResponse:
        rows, total = self.features.list_reports(
            reporter_id=None, status=status, offset=(page - 1) * page_size, limit=page_size
        )
        return ReportListResponse(
            items=[self._read(row) for row in rows], page=page, page_size=page_size, total=total
        )

    def resolve(self, report_id: int, payload: ReportResolve, admin: UserRead) -> ReportRead:
        current = self.features.get_report(report_id)
        if current is None:
            raise AppError(code="REPORT_NOT_FOUND", message="未找到该举报", status_code=404)
        if current.status != ReportStatus.PENDING:
            raise AppError(code="REPORT_ALREADY_HANDLED", message="该举报已经处理", status_code=409)
        if payload.status == ReportStatus.CONTENT_HIDDEN:
            item = self.items.get_by_id(current.item_id)
            if item is not None and item.status == ItemStatus.ACTIVE:
                try:
                    self.items.change_status(
                        item_id=item.id,
                        expected_status=ItemStatus.ACTIVE,
                        new_status=ItemStatus.CLOSED,
                        reason=f"举报 #{report_id} 审核后隐藏：{payload.resolution_note}",
                        changed_by_id=admin.id,
                        changed_at=datetime.now(UTC),
                    )
                except ConcurrentItemUpdateError as exc:
                    raise AppError(
                        code="ITEM_UPDATE_CONFLICT",
                        message="关联物品状态已变化，请刷新后重试",
                        status_code=409,
                    ) from exc
        row = self.features.resolve_report(
            report_id=report_id,
            status=payload.status,
            note=payload.resolution_note,
            admin_id=admin.id,
            now=datetime.now(UTC),
        )
        assert row is not None
        self.features.create_audit(
            actor_id=admin.id,
            action="report.resolve",
            object_type="report",
            object_id=str(report_id),
            reason=payload.resolution_note,
            details={"status": payload.status.value, "item_id": row.item_id},
        )
        return self._read(row)

    @staticmethod
    def _read(row: ReportRecord) -> ReportRead:
        return ReportRead(**{field: getattr(row, field) for field in row.__dataclass_fields__})


class MatchingService:
    """计算可解释候选分数并管理用户通知与反馈。"""

    def __init__(
        self,
        features: FeatureRepository,
        items: ItemRepository,
        ai_matcher: MultimodalMatcher | None = None,
    ) -> None:
        self.features = features
        self.items = items
        self.ai_matcher = ai_matcher

    def generate_for_item(self, item: ItemRecord) -> None:
        """为新发布记录和候选记录的双方所有者创建去重通知。"""

        ranked = [
            (candidate, *self._score(item, candidate))
            for candidate in self.items.list_matching_candidates(source=item)
        ]
        ranked.sort(key=lambda row: (row[1], row[0].id), reverse=True)
        assessments = (
            self.ai_matcher.assess(item, [row[0] for row in ranked]) if self.ai_matcher else {}
        )
        for candidate, score, dimensions in ranked:
            if assessment := assessments.get(candidate.id):
                weight = self.ai_matcher.settings.matching_ai_weight
                score = round(score * (1 - weight) + assessment.score * weight)
                dimensions.append({
                    "label": "AI 图文",
                    "score": assessment.score,
                    "explanation": assessment.explanation,
                })
            if score < 55:
                continue
            if item.owner_id is not None:
                self.features.create_match(
                    recipient_id=item.owner_id,
                    source_item_id=item.id,
                    candidate_item_id=candidate.id,
                    score=score,
                    dimensions=dimensions,
                )
            if candidate.owner_id is not None:
                self.features.create_match(
                    recipient_id=candidate.owner_id,
                    source_item_id=candidate.id,
                    candidate_item_id=item.id,
                    score=score,
                    dimensions=dimensions,
                )

    def list(self, user: UserRead, page: int, page_size: int) -> MatchNotificationListResponse:
        rows, total, unread = self.features.list_matches(
            recipient_id=user.id, offset=(page - 1) * page_size, limit=page_size
        )
        return MatchNotificationListResponse(
            items=[self._read(row, user.id) for row in rows],
            page=page,
            page_size=page_size,
            total=total,
            unread=unread,
        )

    def get(self, match_id: int, user: UserRead) -> MatchNotificationRead:
        row = self.features.get_match(match_id)
        if row is None or row.recipient_id != user.id:
            raise AppError(code="MATCH_NOT_FOUND", message="未找到该匹配通知", status_code=404)
        return self._read(row, user.id)

    def mark_read(self, match_id: int, user: UserRead) -> MatchNotificationRead:
        row = self.features.mark_match_read(match_id=match_id, recipient_id=user.id)
        if row is None:
            raise AppError(code="MATCH_NOT_FOUND", message="未找到该匹配通知", status_code=404)
        return self._read(row, user.id)

    def feedback(
        self, match_id: int, payload: MatchFeedback, user: UserRead
    ) -> MatchNotificationRead:
        current = self.features.get_match(match_id)
        if current is None or current.recipient_id != user.id:
            raise AppError(code="MATCH_NOT_FOUND", message="未找到该匹配通知", status_code=404)
        if current.status != MatchStatus.PENDING:
            raise AppError(code="MATCH_ALREADY_DECIDED", message="该候选已经处理", status_code=409)
        row = self.features.decide_match(
            match_id=match_id,
            recipient_id=user.id,
            status=payload.status,
            reason=payload.reason,
            note=payload.note,
        )
        assert row is not None
        return self._read(row, user.id)

    def _read(self, row: MatchRecord, user_id: int) -> MatchNotificationRead:
        source = self.items.get_by_id(row.source_item_id)
        candidate = self.items.get_by_id(row.candidate_item_id)
        if source is None or candidate is None:
            raise AppError(
                code="MATCH_ITEM_NOT_FOUND", message="匹配关联的物品记录已不存在", status_code=404
            )
        return MatchNotificationRead(
            id=row.id,
            title=f"发现一条{candidate.category}候选线索",
            summary=(
                "系统结合规则与 AI 图文比较生成候选，请核对后反馈。"
                if any(dimension["label"] == "AI 图文" for dimension in row.dimensions)
                else "系统根据物品特征、地点距离和时间生成候选，请核对后反馈。"
            ),
            created_at=row.created_at,
            is_read=row.is_read,
            status=row.status,
            mine=self._public(source),
            candidate=self._public(candidate),
            score=row.score,
            dimensions=[MatchDimension(**dimension) for dimension in row.dimensions],
            rejection_reason=row.rejection_reason,
            rejection_note=row.rejection_note,
        )

    @staticmethod
    def _score(source: ItemRecord, candidate: ItemRecord) -> tuple[int, list[dict[str, object]]]:
        category = 100 if source.category.casefold() == candidate.category.casefold() else 20
        location = campus_distance_table().assess(source, candidate)
        hours = abs((source.occurred_at - candidate.occurred_at).total_seconds()) / 3600
        time_score = max(0, round(100 - min(hours, 168) / 168 * 100))
        source_words = set(source.title.casefold()) | set(source.description.casefold())
        candidate_words = set(candidate.title.casefold()) | set(candidate.description.casefold())
        text = round(
            100 * len(source_words & candidate_words) / max(1, len(source_words | candidate_words))
        )
        # 用实地距离替换原来的校区20%+区域15%；缺坐标时不伪造距离分。
        weighted = category * 0.35 + time_score * 0.20 + text * 0.10
        score = round(
            weighted + location.score * 0.35 if location.score is not None else weighted
        )
        values = [
            ("类别", category, 35),
            ("时间", time_score, 20),
            ("文本", text, 10),
        ]
        return score, [
            {
                "label": label,
                "score": value,
                "explanation": (
                    f"{label}相似度由结构化规则计算，基础权重 {weight}%；"
                    + ("地点未评估时不计入地点分。" if location.score is None else "")
                ),
            }
            for label, value, weight in values
        ] + [{
            "label": "地点",
            "score": location.score,
            "explanation": location.explanation + " 基础权重 35%，500 米时为 50 分。",
        }]

    def _public(self, item: ItemRecord) -> ItemRead:
        """构造匹配对比需要的公开物品字段和图片地址。"""

        return ItemRead(
            id=item.id,
            type=item.type,
            category=item.category,
            title=item.title,
            description=item.description,
            location=item.location,
            campus=item.campus,
            area=item.area,
            occurred_at=item.occurred_at,
            status=item.status,
            contact_hint=item.contact_hint,
            image_urls=[
                f"/api/v1/uploads/images/{image.id}"
                for image in self.features.list_item_images(item.id)
            ],
        )


class AdminService:
    """编排管理端用户、概览、审计和校准版本生命周期。"""

    def __init__(
        self, auth: AuthRepository, items: ItemRepository, features: FeatureRepository
    ) -> None:
        self.auth = auth
        self.items = items
        self.features = features

    def overview(self) -> OverviewRead:
        users, total = self.auth.list_users(keyword=None, status=None, offset=0, limit=1)
        _, restricted = self.auth.list_users(
            keyword=None, status=UserStatus.RESTRICTED, offset=0, limit=1
        )
        item_counts = self.items.count_by_status()
        feature_counts = self.features.feature_counts()
        return OverviewRead(
            users_total=total,
            users_restricted=restricted,
            items_total=sum(item_counts.values()),
            items_active=item_counts.get(ItemStatus.ACTIVE, 0),
            **feature_counts,
        )

    def list_users(
        self, keyword: str | None, status: UserStatus | None, page: int, page_size: int
    ) -> AdminUserListResponse:
        rows, total = self.auth.list_users(
            keyword=keyword, status=status, offset=(page - 1) * page_size, limit=page_size
        )
        return AdminUserListResponse(
            items=[self._user(row) for row in rows], page=page, page_size=page_size, total=total
        )

    def update_user_status(
        self, user_id: int, payload: UserStatusUpdate, admin: UserRead
    ) -> UserRead:
        target = self.auth.get_user_by_id(user_id)
        if target is None:
            raise AppError(code="USER_NOT_FOUND", message="未找到该用户", status_code=404)
        if target.id == admin.id or target.role == UserRole.ADMIN:
            raise AppError(
                code="ADMIN_STATUS_PROTECTED", message="不能修改管理员账号状态", status_code=409
            )
        updated = self.auth.set_user_status(user_id=user_id, status=payload.status)
        assert updated is not None
        self.features.create_audit(
            actor_id=admin.id,
            action="user.status.update",
            object_type="user",
            object_id=str(user_id),
            reason=payload.reason,
            details={"old_status": target.status.value, "new_status": payload.status.value},
        )
        return self._user(updated)

    def list_audits(
        self, action: str | None, object_type: str | None, page: int, page_size: int
    ) -> AuditLogListResponse:
        rows, total = self.features.list_audits(
            action=action, object_type=object_type, offset=(page - 1) * page_size, limit=page_size
        )
        return AuditLogListResponse(
            items=[self._audit(row) for row in rows], page=page, page_size=page_size, total=total
        )

    def create_calibration(
        self, payload: CalibrationTaskCreate, admin: UserRead
    ) -> CalibrationTaskRead:
        task, version = self.features.create_calibration(
            category=payload.category,
            range_start=payload.range_start,
            range_end=payload.range_end,
            admin_id=admin.id,
            now=datetime.now(UTC),
        )
        self.features.create_audit(
            actor_id=admin.id,
            action="calibration.create",
            object_type="calibration_version",
            object_id=str(version.id),
            reason="创建匹配校准任务",
            details={"task_id": task.id},
        )
        return self._task(task)

    def list_calibration_tasks(self) -> list[CalibrationTaskRead]:
        return [self._task(row) for row in self.features.list_calibration_tasks()]

    def list_calibration_versions(self) -> list[CalibrationVersionRead]:
        return [self._version(row) for row in self.features.list_calibration_versions()]

    def change_calibration(
        self, version_id: int, payload: CalibrationVersionAction, admin: UserRead
    ) -> CalibrationVersionRead:
        row = self.features.change_calibration_version(
            version_id=version_id, action=payload.action, admin_id=admin.id, reason=payload.reason
        )
        if row is None:
            raise AppError(
                code="CALIBRATION_TRANSITION_INVALID",
                message="版本不存在或当前状态不允许该操作",
                status_code=409,
            )
        self.features.create_audit(
            actor_id=admin.id,
            action=f"calibration.{payload.action}",
            object_type="calibration_version",
            object_id=str(version_id),
            reason=payload.reason,
            details={"status": row.status.value},
        )
        return self._version(row)

    @staticmethod
    def _user(row: UserRecord) -> UserRead:
        return UserRead(
            id=row.id,
            account=row.account,
            display_name=row.display_name,
            role=row.role,
            status=row.status,
            campus_verified=row.campus_verified,
            created_at=row.created_at,
        )

    @staticmethod
    def _audit(row: AuditRecord) -> AuditLogRead:
        return AuditLogRead(**{field: getattr(row, field) for field in row.__dataclass_fields__})

    @staticmethod
    def _task(row: CalibrationTaskRecord) -> CalibrationTaskRead:
        return CalibrationTaskRead(
            **{field: getattr(row, field) for field in row.__dataclass_fields__}
        )

    @staticmethod
    def _version(row: CalibrationVersionRecord) -> CalibrationVersionRead:
        return CalibrationVersionRead(
            **{field: getattr(row, field) for field in row.__dataclass_fields__}
        )
