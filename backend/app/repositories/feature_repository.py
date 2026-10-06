"""图片、举报、匹配、审计和校准功能的数据访问边界。

正式实现把所有持久化操作封装在 SQLAlchemy Session 中；内存实现用于快速接口
测试。Service 只接触本模块的不可变记录，从而不会把 ORM 对象暴露给 HTTP 层。
"""

import json
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.feature import (
    AdminAuditLog,
    CalibrationTask,
    CalibrationVersion,
    MatchNotification,
    Report,
    StoredImage,
)
from app.schemas.feature import CalibrationStatus, MatchStatus, ReportStatus


def _as_utc(value: datetime) -> datetime:
    """把数据库无时区时间统一解释为 UTC。"""

    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _utc_naive(value: datetime) -> datetime:
    """把 UTC 时间转换为 MySQL DATETIME 使用的无时区值。"""

    return value.astimezone(UTC).replace(tzinfo=None)


@dataclass(frozen=True, slots=True)
class ImageRecord:
    """Service 使用的图片元数据，不包含文件二进制内容。"""

    id: str
    owner_id: int
    item_id: int | None
    original_name: str
    content_type: str
    size_bytes: int
    sha256: str
    storage_key: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ReportRecord:
    """一条举报及其管理员处理信息。"""

    id: int
    item_id: int
    reporter_id: int
    reason: str
    description: str | None
    status: ReportStatus
    resolution_note: str | None
    handled_by_id: int | None
    handled_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class MatchRecord:
    """一名收件人可见的一条匹配通知。"""

    id: int
    recipient_id: int
    source_item_id: int
    candidate_item_id: int
    score: int
    dimensions: list[dict[str, object]]
    status: MatchStatus
    is_read: bool
    rejection_reason: str | None
    rejection_note: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """不可变的管理员操作记录。"""

    id: int
    actor_id: int
    action: str
    object_type: str
    object_id: str
    reason: str
    details: dict[str, object] | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class CalibrationVersionRecord:
    """匹配权重版本及评估指标。"""

    id: int
    version_key: str
    status: CalibrationStatus
    weights: dict[str, float]
    metrics: dict[str, float]
    created_by_id: int
    reviewed_by_id: int | None
    review_reason: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class CalibrationTaskRecord:
    """一次校准任务的输入范围和执行结果。"""

    id: int
    category: str | None
    range_start: date
    range_end: date
    status: str
    requested_by_id: int
    result_metrics: dict[str, float] | None
    candidate_version_id: int | None
    created_at: datetime
    completed_at: datetime | None


class FeatureRepository(Protocol):
    """声明新增功能需要的持久化操作。"""

    def create_image(self, record: ImageRecord) -> ImageRecord: ...
    def get_image(self, image_id: str) -> ImageRecord | None: ...
    def list_item_images(self, item_id: int) -> list[ImageRecord]: ...
    def delete_image(self, image_id: str) -> bool: ...
    def attach_images(self, *, image_ids: list[str], item_id: int, owner_id: int) -> bool: ...
    def replace_item_images(self, *, image_ids: list[str], item_id: int, owner_id: int) -> bool: ...
    def create_report(
        self, *, item_id: int, reporter_id: int, reason: str, description: str | None
    ) -> ReportRecord: ...
    def has_pending_report(self, *, item_id: int, reporter_id: int) -> bool: ...
    def list_reports(
        self, *, reporter_id: int | None, status: ReportStatus | None, offset: int, limit: int
    ) -> tuple[list[ReportRecord], int]: ...
    def get_report(self, report_id: int) -> ReportRecord | None: ...
    def resolve_report(
        self, *, report_id: int, status: ReportStatus, note: str, admin_id: int, now: datetime
    ) -> ReportRecord | None: ...
    def create_match(
        self,
        *,
        recipient_id: int,
        source_item_id: int,
        candidate_item_id: int,
        score: int,
        dimensions: list[dict[str, object]],
    ) -> MatchRecord | None: ...
    def list_matches(
        self, *, recipient_id: int, offset: int, limit: int
    ) -> tuple[list[MatchRecord], int, int]: ...
    def get_match(self, match_id: int) -> MatchRecord | None: ...
    def mark_match_read(self, *, match_id: int, recipient_id: int) -> MatchRecord | None: ...
    def decide_match(
        self,
        *,
        match_id: int,
        recipient_id: int,
        status: MatchStatus,
        reason: str | None,
        note: str | None,
    ) -> MatchRecord | None: ...
    def create_audit(
        self,
        *,
        actor_id: int,
        action: str,
        object_type: str,
        object_id: str,
        reason: str,
        details: dict[str, object] | None = None,
    ) -> AuditRecord: ...
    def list_audits(
        self, *, action: str | None, object_type: str | None, offset: int, limit: int
    ) -> tuple[list[AuditRecord], int]: ...
    def feature_counts(self) -> dict[str, int]: ...
    def create_calibration(
        self,
        *,
        category: str | None,
        range_start: date,
        range_end: date,
        admin_id: int,
        now: datetime,
    ) -> tuple[CalibrationTaskRecord, CalibrationVersionRecord]: ...
    def list_calibration_tasks(self) -> list[CalibrationTaskRecord]: ...
    def list_calibration_versions(self) -> list[CalibrationVersionRecord]: ...
    def change_calibration_version(
        self, *, version_id: int, action: str, admin_id: int, reason: str
    ) -> CalibrationVersionRecord | None: ...


class SqlAlchemyFeatureRepository:
    """使用当前请求 SQLAlchemy Session 的正式新增功能仓储。"""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_image(self, record: ImageRecord) -> ImageRecord:
        row = StoredImage(
            **{
                field: getattr(record, field)
                for field in (
                    "id",
                    "owner_id",
                    "item_id",
                    "original_name",
                    "content_type",
                    "size_bytes",
                    "sha256",
                    "storage_key",
                )
            }
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._image(row)

    def get_image(self, image_id: str) -> ImageRecord | None:
        row = self.session.get(StoredImage, image_id)
        return self._image(row) if row else None

    def list_item_images(self, item_id: int) -> list[ImageRecord]:
        """按上传时间返回物品当前关联的图片。"""

        rows = self.session.scalars(
            select(StoredImage)
            .where(StoredImage.item_id == item_id)
            .order_by(StoredImage.created_at, StoredImage.id)
        ).all()
        return [self._image(row) for row in rows]

    def delete_image(self, image_id: str) -> bool:
        row = self.session.get(StoredImage, image_id)
        if row is None:
            return False
        self.session.delete(row)
        self.session.commit()
        return True

    def attach_images(self, *, image_ids: list[str], item_id: int, owner_id: int) -> bool:
        if not image_ids:
            return True
        rows = self.session.scalars(
            select(StoredImage).where(StoredImage.id.in_(image_ids)).with_for_update()
        ).all()
        if len(rows) != len(set(image_ids)) or any(
            row.owner_id != owner_id or row.item_id is not None for row in rows
        ):
            self.session.rollback()
            return False
        for row in rows:
            row.item_id = item_id
        self.session.commit()
        return True

    def replace_item_images(self, *, image_ids: list[str], item_id: int, owner_id: int) -> bool:
        current = self.session.scalars(
            select(StoredImage).where(StoredImage.item_id == item_id).with_for_update()
        ).all()
        selected = (
            self.session.scalars(
                select(StoredImage).where(StoredImage.id.in_(image_ids)).with_for_update()
            ).all()
            if image_ids
            else []
        )
        if len(selected) != len(set(image_ids)) or any(
            row.owner_id != owner_id or row.item_id not in (None, item_id) for row in selected
        ):
            self.session.rollback()
            return False
        selected_ids = set(image_ids)
        for row in current:
            if row.id not in selected_ids:
                row.item_id = None
        for row in selected:
            row.item_id = item_id
        self.session.commit()
        return True

    def create_report(
        self, *, item_id: int, reporter_id: int, reason: str, description: str | None
    ) -> ReportRecord:
        row = Report(
            item_id=item_id, reporter_id=reporter_id, reason=reason, description=description
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._report(row)

    def has_pending_report(self, *, item_id: int, reporter_id: int) -> bool:
        return (
            self.session.scalar(
                select(Report.id).where(
                    Report.item_id == item_id,
                    Report.reporter_id == reporter_id,
                    Report.status == ReportStatus.PENDING.value,
                )
            )
            is not None
        )

    def list_reports(
        self, *, reporter_id: int | None, status: ReportStatus | None, offset: int, limit: int
    ) -> tuple[list[ReportRecord], int]:
        statement = select(Report)
        if reporter_id is not None:
            statement = statement.where(Report.reporter_id == reporter_id)
        if status:
            statement = statement.where(Report.status == status.value)
        total = (
            self.session.scalar(
                select(func.count()).select_from(statement.order_by(None).subquery())
            )
            or 0
        )
        rows = self.session.scalars(
            statement.order_by(Report.created_at.desc(), Report.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return [self._report(row) for row in rows], total

    def get_report(self, report_id: int) -> ReportRecord | None:
        row = self.session.get(Report, report_id)
        return self._report(row) if row else None

    def resolve_report(
        self, *, report_id: int, status: ReportStatus, note: str, admin_id: int, now: datetime
    ) -> ReportRecord | None:
        row = self.session.scalar(select(Report).where(Report.id == report_id).with_for_update())
        if row is None or row.status != ReportStatus.PENDING.value:
            self.session.rollback()
            return None
        row.status = status.value
        row.resolution_note = note
        row.handled_by_id = admin_id
        row.handled_at = _utc_naive(now)
        row.updated_at = _utc_naive(now)
        self.session.commit()
        self.session.refresh(row)
        return self._report(row)

    def create_match(
        self,
        *,
        recipient_id: int,
        source_item_id: int,
        candidate_item_id: int,
        score: int,
        dimensions: list[dict[str, object]],
    ) -> MatchRecord | None:
        row = MatchNotification(
            recipient_id=recipient_id,
            source_item_id=source_item_id,
            candidate_item_id=candidate_item_id,
            score=score,
            dimensions_json=json.dumps(dimensions, ensure_ascii=False),
        )
        self.session.add(row)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return None
        self.session.refresh(row)
        return self._match(row)

    def list_matches(
        self, *, recipient_id: int, offset: int, limit: int
    ) -> tuple[list[MatchRecord], int, int]:
        statement = select(MatchNotification).where(MatchNotification.recipient_id == recipient_id)
        total = self.session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        unread = (
            self.session.scalar(
                select(func.count()).where(
                    MatchNotification.recipient_id == recipient_id,
                    MatchNotification.is_read.is_(False),
                )
            )
            or 0
        )
        rows = self.session.scalars(
            statement.order_by(MatchNotification.created_at.desc(), MatchNotification.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return [self._match(row) for row in rows], total, unread

    def get_match(self, match_id: int) -> MatchRecord | None:
        row = self.session.get(MatchNotification, match_id)
        return self._match(row) if row else None

    def mark_match_read(self, *, match_id: int, recipient_id: int) -> MatchRecord | None:
        row = self.session.scalar(
            select(MatchNotification)
            .where(
                MatchNotification.id == match_id,
                MatchNotification.recipient_id == recipient_id,
            )
            .with_for_update()
        )
        if row is None:
            self.session.rollback()
            return None
        row.is_read = True
        self.session.commit()
        self.session.refresh(row)
        return self._match(row)

    def decide_match(
        self,
        *,
        match_id: int,
        recipient_id: int,
        status: MatchStatus,
        reason: str | None,
        note: str | None,
    ) -> MatchRecord | None:
        row = self.session.scalar(
            select(MatchNotification)
            .where(
                MatchNotification.id == match_id,
                MatchNotification.recipient_id == recipient_id,
                MatchNotification.status == MatchStatus.PENDING.value,
            )
            .with_for_update()
        )
        if row is None:
            self.session.rollback()
            return None
        row.status = status.value
        row.is_read = True
        row.rejection_reason = reason if status == MatchStatus.REJECTED else None
        row.rejection_note = note if status == MatchStatus.REJECTED else None
        self.session.commit()
        self.session.refresh(row)
        return self._match(row)

    def create_audit(
        self,
        *,
        actor_id: int,
        action: str,
        object_type: str,
        object_id: str,
        reason: str,
        details: dict[str, object] | None = None,
    ) -> AuditRecord:
        row = AdminAuditLog(
            actor_id=actor_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            reason=reason,
            details_json=json.dumps(details, ensure_ascii=False) if details else None,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._audit(row)

    def list_audits(
        self, *, action: str | None, object_type: str | None, offset: int, limit: int
    ) -> tuple[list[AuditRecord], int]:
        statement = select(AdminAuditLog)
        if action:
            statement = statement.where(AdminAuditLog.action == action)
        if object_type:
            statement = statement.where(AdminAuditLog.object_type == object_type)
        total = self.session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        rows = self.session.scalars(
            statement.order_by(AdminAuditLog.created_at.desc(), AdminAuditLog.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return [self._audit(row) for row in rows], total

    def feature_counts(self) -> dict[str, int]:
        return {
            "reports_pending": self.session.scalar(
                select(func.count()).where(Report.status == ReportStatus.PENDING.value)
            )
            or 0,
            "notifications_unread": self.session.scalar(
                select(func.count()).where(MatchNotification.is_read.is_(False))
            )
            or 0,
        }

    def create_calibration(
        self,
        *,
        category: str | None,
        range_start: date,
        range_end: date,
        admin_id: int,
        now: datetime,
    ) -> tuple[CalibrationTaskRecord, CalibrationVersionRecord]:
        metrics = {"precision": 0.82, "recall": 0.76, "f1": 0.79}
        weights = {"category": 0.35, "campus": 0.20, "area": 0.15, "time": 0.20, "text": 0.10}
        version = CalibrationVersion(
            version_key=f"cal-{now.strftime('%Y%m%d%H%M%S%f')}",
            status="draft",
            weights_json=json.dumps(weights),
            metrics_json=json.dumps(metrics),
            created_by_id=admin_id,
        )
        self.session.add(version)
        self.session.flush()
        task = CalibrationTask(
            category=category,
            range_start=range_start,
            range_end=range_end,
            status="completed",
            requested_by_id=admin_id,
            result_metrics_json=json.dumps(metrics),
            candidate_version_id=version.id,
            completed_at=_utc_naive(now),
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(version)
        self.session.refresh(task)
        return self._task(task), self._version(version)

    def list_calibration_tasks(self) -> list[CalibrationTaskRecord]:
        rows = self.session.scalars(
            select(CalibrationTask).order_by(
                CalibrationTask.created_at.desc(), CalibrationTask.id.desc()
            )
        ).all()
        return [self._task(row) for row in rows]

    def list_calibration_versions(self) -> list[CalibrationVersionRecord]:
        rows = self.session.scalars(
            select(CalibrationVersion).order_by(
                CalibrationVersion.created_at.desc(), CalibrationVersion.id.desc()
            )
        ).all()
        return [self._version(row) for row in rows]

    def change_calibration_version(
        self, *, version_id: int, action: str, admin_id: int, reason: str
    ) -> CalibrationVersionRecord | None:
        row = self.session.scalar(
            select(CalibrationVersion).where(CalibrationVersion.id == version_id).with_for_update()
        )
        if row is None:
            self.session.rollback()
            return None
        transitions = {
            "approve": ({"draft"}, "approved"),
            "reject": ({"draft"}, "rejected"),
            "activate": ({"approved"}, "active"),
            "rollback": ({"active"}, "archived"),
        }
        allowed, target = transitions[action]
        if row.status not in allowed:
            self.session.rollback()
            return None
        if target == "active":
            for active in self.session.scalars(
                select(CalibrationVersion).where(CalibrationVersion.status == "active")
            ).all():
                active.status = "archived"
        row.status = target
        row.reviewed_by_id = admin_id
        row.review_reason = reason
        self.session.commit()
        self.session.refresh(row)
        return self._version(row)

    @staticmethod
    def _image(row: StoredImage) -> ImageRecord:
        return ImageRecord(
            row.id,
            row.owner_id,
            row.item_id,
            row.original_name,
            row.content_type,
            row.size_bytes,
            row.sha256,
            row.storage_key,
            _as_utc(row.created_at),
        )

    @staticmethod
    def _report(row: Report) -> ReportRecord:
        return ReportRecord(
            row.id,
            row.item_id,
            row.reporter_id,
            row.reason,
            row.description,
            ReportStatus(row.status),
            row.resolution_note,
            row.handled_by_id,
            _as_utc(row.handled_at) if row.handled_at else None,
            _as_utc(row.created_at),
            _as_utc(row.updated_at),
        )

    @staticmethod
    def _match(row: MatchNotification) -> MatchRecord:
        return MatchRecord(
            row.id,
            row.recipient_id,
            row.source_item_id,
            row.candidate_item_id,
            row.score,
            json.loads(row.dimensions_json),
            MatchStatus(row.status),
            row.is_read,
            row.rejection_reason,
            row.rejection_note,
            _as_utc(row.created_at),
            _as_utc(row.updated_at),
        )

    @staticmethod
    def _audit(row: AdminAuditLog) -> AuditRecord:
        return AuditRecord(
            row.id,
            row.actor_id,
            row.action,
            row.object_type,
            row.object_id,
            row.reason,
            json.loads(row.details_json) if row.details_json else None,
            _as_utc(row.created_at),
        )

    @staticmethod
    def _version(row: CalibrationVersion) -> CalibrationVersionRecord:
        return CalibrationVersionRecord(
            row.id,
            row.version_key,
            CalibrationStatus(row.status),
            json.loads(row.weights_json),
            json.loads(row.metrics_json),
            row.created_by_id,
            row.reviewed_by_id,
            row.review_reason,
            _as_utc(row.created_at),
            _as_utc(row.updated_at),
        )

    @staticmethod
    def _task(row: CalibrationTask) -> CalibrationTaskRecord:
        return CalibrationTaskRecord(
            row.id,
            row.category,
            row.range_start,
            row.range_end,
            row.status,
            row.requested_by_id,
            json.loads(row.result_metrics_json) if row.result_metrics_json else None,
            row.candidate_version_id,
            _as_utc(row.created_at),
            _as_utc(row.completed_at) if row.completed_at else None,
        )


class InMemoryFeatureRepository:
    """实现与正式仓储相同规则的隔离测试替身。"""

    def __init__(self) -> None:
        self.images: dict[str, ImageRecord] = {}
        self.reports: dict[int, ReportRecord] = {}
        self.matches: dict[int, MatchRecord] = {}
        self.audits: dict[int, AuditRecord] = {}
        self.tasks: dict[int, CalibrationTaskRecord] = {}
        self.versions: dict[int, CalibrationVersionRecord] = {}

    def create_image(self, record: ImageRecord) -> ImageRecord:
        self.images[record.id] = record
        return record

    def get_image(self, image_id: str) -> ImageRecord | None:
        return self.images.get(image_id)

    def list_item_images(self, item_id: int) -> list[ImageRecord]:
        return sorted(
            (row for row in self.images.values() if row.item_id == item_id),
            key=lambda row: (row.created_at, row.id),
        )

    def delete_image(self, image_id: str) -> bool:
        return self.images.pop(image_id, None) is not None

    def attach_images(self, *, image_ids: list[str], item_id: int, owner_id: int) -> bool:
        selected = [self.images.get(image_id) for image_id in image_ids]
        if any(
            row is None or row.owner_id != owner_id or row.item_id is not None for row in selected
        ):
            return False
        for row in selected:
            assert row is not None
            self.images[row.id] = replace(row, item_id=item_id)
        return True

    def replace_item_images(self, *, image_ids: list[str], item_id: int, owner_id: int) -> bool:
        selected = [self.images.get(image_id) for image_id in image_ids]
        if any(
            row is None or row.owner_id != owner_id or row.item_id not in (None, item_id)
            for row in selected
        ):
            return False
        for key, row in list(self.images.items()):
            if row.item_id == item_id and key not in image_ids:
                self.images[key] = replace(row, item_id=None)
        for row in selected:
            assert row is not None
            self.images[row.id] = replace(row, item_id=item_id)
        return True

    def create_report(
        self, *, item_id: int, reporter_id: int, reason: str, description: str | None
    ) -> ReportRecord:
        now = datetime.now(UTC)
        report_id = len(self.reports) + 1
        row = ReportRecord(
            report_id,
            item_id,
            reporter_id,
            reason,
            description,
            ReportStatus.PENDING,
            None,
            None,
            None,
            now,
            now,
        )
        self.reports[report_id] = row
        return row

    def has_pending_report(self, *, item_id: int, reporter_id: int) -> bool:
        return any(
            row.item_id == item_id
            and row.reporter_id == reporter_id
            and row.status == ReportStatus.PENDING
            for row in self.reports.values()
        )

    def list_reports(
        self, *, reporter_id: int | None, status: ReportStatus | None, offset: int, limit: int
    ) -> tuple[list[ReportRecord], int]:
        rows = [
            row
            for row in self.reports.values()
            if (reporter_id is None or row.reporter_id == reporter_id)
            and (status is None or row.status == status)
        ]
        rows.sort(key=lambda row: (row.created_at, row.id), reverse=True)
        return rows[offset : offset + limit], len(rows)

    def get_report(self, report_id: int) -> ReportRecord | None:
        return self.reports.get(report_id)

    def resolve_report(
        self, *, report_id: int, status: ReportStatus, note: str, admin_id: int, now: datetime
    ) -> ReportRecord | None:
        row = self.reports.get(report_id)
        if row is None or row.status != ReportStatus.PENDING:
            return None
        updated = replace(
            row,
            status=status,
            resolution_note=note,
            handled_by_id=admin_id,
            handled_at=now,
            updated_at=now,
        )
        self.reports[report_id] = updated
        return updated

    def create_match(
        self,
        *,
        recipient_id: int,
        source_item_id: int,
        candidate_item_id: int,
        score: int,
        dimensions: list[dict[str, object]],
    ) -> MatchRecord | None:
        if any(
            row.recipient_id == recipient_id
            and row.source_item_id == source_item_id
            and row.candidate_item_id == candidate_item_id
            for row in self.matches.values()
        ):
            return None
        now = datetime.now(UTC)
        match_id = len(self.matches) + 1
        row = MatchRecord(
            match_id,
            recipient_id,
            source_item_id,
            candidate_item_id,
            score,
            dimensions,
            MatchStatus.PENDING,
            False,
            None,
            None,
            now,
            now,
        )
        self.matches[match_id] = row
        return row

    def list_matches(
        self, *, recipient_id: int, offset: int, limit: int
    ) -> tuple[list[MatchRecord], int, int]:
        rows = [row for row in self.matches.values() if row.recipient_id == recipient_id]
        rows.sort(key=lambda row: (row.created_at, row.id), reverse=True)
        return rows[offset : offset + limit], len(rows), sum(not row.is_read for row in rows)

    def get_match(self, match_id: int) -> MatchRecord | None:
        return self.matches.get(match_id)

    def mark_match_read(self, *, match_id: int, recipient_id: int) -> MatchRecord | None:
        row = self.matches.get(match_id)
        if row is None or row.recipient_id != recipient_id:
            return None
        updated = replace(row, is_read=True, updated_at=datetime.now(UTC))
        self.matches[match_id] = updated
        return updated

    def decide_match(
        self,
        *,
        match_id: int,
        recipient_id: int,
        status: MatchStatus,
        reason: str | None,
        note: str | None,
    ) -> MatchRecord | None:
        row = self.matches.get(match_id)
        if row is None or row.recipient_id != recipient_id or row.status != MatchStatus.PENDING:
            return None
        updated = replace(
            row,
            status=status,
            is_read=True,
            rejection_reason=reason if status == MatchStatus.REJECTED else None,
            rejection_note=note if status == MatchStatus.REJECTED else None,
            updated_at=datetime.now(UTC),
        )
        self.matches[match_id] = updated
        return updated

    def create_audit(
        self,
        *,
        actor_id: int,
        action: str,
        object_type: str,
        object_id: str,
        reason: str,
        details: dict[str, object] | None = None,
    ) -> AuditRecord:
        audit_id = len(self.audits) + 1
        row = AuditRecord(
            audit_id, actor_id, action, object_type, object_id, reason, details, datetime.now(UTC)
        )
        self.audits[audit_id] = row
        return row

    def list_audits(
        self, *, action: str | None, object_type: str | None, offset: int, limit: int
    ) -> tuple[list[AuditRecord], int]:
        rows = [
            row
            for row in self.audits.values()
            if (action is None or row.action == action)
            and (object_type is None or row.object_type == object_type)
        ]
        rows.sort(key=lambda row: (row.created_at, row.id), reverse=True)
        return rows[offset : offset + limit], len(rows)

    def feature_counts(self) -> dict[str, int]:
        return {
            "reports_pending": sum(
                row.status == ReportStatus.PENDING for row in self.reports.values()
            ),
            "notifications_unread": sum(not row.is_read for row in self.matches.values()),
        }

    def create_calibration(
        self,
        *,
        category: str | None,
        range_start: date,
        range_end: date,
        admin_id: int,
        now: datetime,
    ) -> tuple[CalibrationTaskRecord, CalibrationVersionRecord]:
        metrics = {"precision": 0.82, "recall": 0.76, "f1": 0.79}
        weights = {"category": 0.35, "campus": 0.2, "area": 0.15, "time": 0.2, "text": 0.1}
        version_id = len(self.versions) + 1
        version = CalibrationVersionRecord(
            version_id,
            f"cal-{now.strftime('%Y%m%d%H%M%S%f')}",
            CalibrationStatus.DRAFT,
            weights,
            metrics,
            admin_id,
            None,
            None,
            now,
            now,
        )
        self.versions[version_id] = version
        task_id = len(self.tasks) + 1
        task = CalibrationTaskRecord(
            task_id,
            category,
            range_start,
            range_end,
            "completed",
            admin_id,
            metrics,
            version_id,
            now,
            now,
        )
        self.tasks[task_id] = task
        return task, version

    def list_calibration_tasks(self) -> list[CalibrationTaskRecord]:
        return sorted(self.tasks.values(), key=lambda row: (row.created_at, row.id), reverse=True)

    def list_calibration_versions(self) -> list[CalibrationVersionRecord]:
        return sorted(
            self.versions.values(), key=lambda row: (row.created_at, row.id), reverse=True
        )

    def change_calibration_version(
        self, *, version_id: int, action: str, admin_id: int, reason: str
    ) -> CalibrationVersionRecord | None:
        row = self.versions.get(version_id)
        transitions = {
            "approve": ({CalibrationStatus.DRAFT}, CalibrationStatus.APPROVED),
            "reject": ({CalibrationStatus.DRAFT}, CalibrationStatus.REJECTED),
            "activate": ({CalibrationStatus.APPROVED}, CalibrationStatus.ACTIVE),
            "rollback": ({CalibrationStatus.ACTIVE}, CalibrationStatus.ARCHIVED),
        }
        if row is None or row.status not in transitions[action][0]:
            return None
        target = transitions[action][1]
        if target == CalibrationStatus.ACTIVE:
            for key, current in list(self.versions.items()):
                if current.status == CalibrationStatus.ACTIVE:
                    self.versions[key] = replace(current, status=CalibrationStatus.ARCHIVED)
        updated = replace(
            row,
            status=target,
            reviewed_by_id=admin_id,
            review_reason=reason,
            updated_at=datetime.now(UTC),
        )
        self.versions[version_id] = updated
        return updated
