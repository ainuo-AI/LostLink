"""多模态供应商、评分融合及发布降级测试；所有请求均由 MockTransport 拦截。"""

import json
from dataclasses import replace
from datetime import UTC, datetime

import httpx
import pytest
from pydantic import ValidationError

from app.api.dependencies import get_matching_service
from app.core.config import Settings
from app.integrations.multimodal_matching import MultimodalMatcher
from app.repositories.feature_repository import ImageRecord
from app.services.feature_service import MatchingService
from tests.api.test_item_management import authenticated_headers, lost_payload
from tests.api.test_remaining_features import found_payload


def ai_settings(tmp_path, **overrides):
    return Settings(
        _env_file=None,
        matching_ai_enabled=True,
        matching_ai_base_url="https://vision.example/v1/",
        matching_ai_api_key="test-key",
        matching_ai_model="test-vision",
        upload_directory=tmp_path,
        **overrides,
    )


def completion(matches, *, fenced=False):
    matches = [
        {"text_score": 82, "text_explanation": "标题和描述的颜色与物品名称接近", **match}
        for match in matches
    ]
    content = json.dumps({"matches": matches}, ensure_ascii=False)
    if fenced:
        content = f"```json\n{content}\n```"
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def attach_image(features, tmp_path, item_id, *, storage_key="proof.png", data=b"photo"):
    (tmp_path / storage_key).write_bytes(data)
    features.create_image(ImageRecord(
        id=f"image-{item_id}", owner_id=1, item_id=item_id,
        original_name="proof.png", content_type="image/png", size_bytes=len(data),
        sha256="example-hash", storage_key=storage_key, created_at=datetime.now(UTC),
    ))


def test_request_sends_labeled_images_and_only_public_fields(
    tmp_path, item_repository, feature_repository,
):
    source = item_repository.get_by_id(1)
    candidate = item_repository.get_by_id(2)
    attach_image(feature_repository, tmp_path, source.id)
    attach_image(feature_repository, tmp_path, candidate.id, storage_key="candidate.png")
    requests = []

    def handler(request):
        requests.append(request)
        assert str(request.url) == "https://vision.example/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        assert body["model"] == "test-vision"
        assert "时间和地点距离由本地规则计算，不要推测距离" in body["messages"][0]["content"]
        assert "不能按共同字符比例评分" in body["messages"][0]["content"]
        assert "不能使用图片、类别字段、时间或地点" in body["messages"][0]["content"]
        content = body["messages"][1]["content"]
        assert [part["type"] for part in content] == [
            "text", "image_url", "text", "image_url",
        ]
        for part in content:
            if part["type"] == "text":
                assert not {"contact", "contact_hint", "owner_id", "closure_reason"} & set(
                    json.loads(part["text"])
                )
            else:
                assert part["image_url"]["url"] == "data:image/png;base64,cGhvdG8="
        return completion([
            {"candidate_id": candidate.id, "score": 83, "explanation": "颜色和外观接近"},
        ], fenced=True)

    matcher = MultimodalMatcher(
        ai_settings(tmp_path), feature_repository, transport=httpx.MockTransport(handler),
    )
    result = matcher.assess(source, [candidate])
    assert result[candidate.id].score == 83
    assert result[candidate.id].text_score == 82
    assert len(requests) == 1


@pytest.mark.parametrize("failure", [
    "timeout", "unauthorized", "rate_limit", "server", "unsupported_images",
    "malformed_json", "missing_content", "score_out_of_range", "unknown_id",
    "duplicate_id", "missing_id", "empty_content",
])
def test_provider_failures_fall_back_without_leaking_secrets(
    tmp_path, item_repository, feature_repository, caplog, failure,
):
    def handler(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("test-key PRIVATE upstream", request=request)
        statuses = {
            "unauthorized": 401, "rate_limit": 429, "server": 503, "unsupported_images": 400,
        }
        if failure in statuses:
            return httpx.Response(statuses[failure], text="test-key PRIVATE upstream")
        if failure == "malformed_json":
            return httpx.Response(200, json={"choices": [{"message": {"content": "invalid"}}]})
        if failure == "missing_content":
            return httpx.Response(200, json={})
        if failure == "empty_content":
            return httpx.Response(200, json={"choices": [{"message": {"content": None}}]})
        rows = [{"candidate_id": 2, "score": 80, "explanation": "外观接近"}]
        if failure == "score_out_of_range":
            rows[0]["score"] = 101
        elif failure == "unknown_id":
            rows[0]["candidate_id"] = 999
        elif failure == "duplicate_id":
            rows *= 2
        else:
            rows = []
        return completion(rows)

    matcher = MultimodalMatcher(
        ai_settings(tmp_path), feature_repository, transport=httpx.MockTransport(handler),
    )
    assert matcher.assess(item_repository.get_by_id(1), [item_repository.get_by_id(2)]) == {}
    assert "using rule scores" in caplog.text
    assert "test-key" not in caplog.text
    assert "PRIVATE" not in caplog.text
    assert matcher.failure_reason is not None
    if failure == "timeout":
        assert "超时" in matcher.failure_reason
    elif failure in {"unauthorized", "rate_limit", "server", "unsupported_images"}:
        assert "HTTP" in matcher.failure_reason
    elif failure in {"unknown_id", "duplicate_id", "missing_id"}:
        assert "候选编号" in matcher.failure_reason


def test_image_budget_and_missing_files_use_text(
    tmp_path, item_repository, feature_repository,
):
    attach_image(feature_repository, tmp_path, 1, data=b"x" * 1025)
    attach_image(feature_repository, tmp_path, 2, storage_key="missing.png")
    (tmp_path / "missing.png").unlink()
    matcher = MultimodalMatcher(
        ai_settings(tmp_path, matching_ai_max_image_bytes=1024), feature_repository,
    )
    content = matcher._content(item_repository.get_by_id(1), [item_repository.get_by_id(2)])
    assert [part["type"] for part in content] == ["text", "text"]


def test_ai_can_raise_candidate_below_rule_threshold(
    tmp_path, item_repository, feature_repository,
):
    # 同校区但类别不同的候选规则分不足 55；AI 应在阈值过滤之前参与融合。
    source = replace(item_repository.get_by_id(1), owner_id=123)
    matcher = MultimodalMatcher(
        ai_settings(tmp_path, matching_ai_weight=1), feature_repository,
        transport=httpx.MockTransport(lambda request: completion([
            {"candidate_id": 2, "score": 88, "explanation": "图片显示相同独特配件"},
        ])),
    )
    service = MatchingService(feature_repository, item_repository, matcher)
    assert service._score(source, item_repository.get_by_id(2))[0] < 55
    service.generate_for_item(source)
    rows, total, _ = feature_repository.list_matches(
        recipient_id=source.owner_id, offset=0, limit=10,
    )
    assert total == 1
    assert rows[0].score == 88
    assert rows[0].dimensions[-1]["label"] == "AI 图文"


@pytest.mark.parametrize("provider_fails", [False, True])
def test_publication_uses_ai_and_still_succeeds_when_provider_fails(
    client, tmp_path, item_repository, feature_repository, provider_fails,
):
    calls = []

    def handler(request):
        calls.append(request)
        if provider_fails:
            return httpx.Response(503)
        content = json.loads(request.content)["messages"][1]["content"]
        candidates = [json.loads(part["text"]) for part in content if part["type"] == "text"]
        return completion([
            {"candidate_id": row["id"], "score": 90, "explanation": "描述中的特征接近"}
            for row in candidates if row["role"] == "candidate"
        ])

    settings = ai_settings(tmp_path, matching_ai_max_candidates=1)
    matcher = MultimodalMatcher(
        settings, feature_repository, transport=httpx.MockTransport(handler),
    )
    client.app.dependency_overrides[get_matching_service] = lambda: MatchingService(
        feature_repository, item_repository, matcher,
    )
    lost_headers, _ = authenticated_headers(client, "ai-lost")
    found_headers, _ = authenticated_headers(client, "ai-found")
    lost = client.post("/api/v1/items", headers=lost_headers, json=lost_payload())
    found = client.post("/api/v1/items", headers=found_headers, json=found_payload())
    assert lost.status_code == found.status_code == 201
    assert len(calls) == 2  # 每次发布至多调用一次（包含原有演示候选）。
    matches = client.get("/api/v1/notifications", headers=lost_headers).json()["items"]
    match = next(row for row in matches if row["candidate"]["id"] == found.json()["id"])
    assert (len(match["dimensions"]) == 4) if provider_fails else (
        match["dimensions"][-1]["label"] == "AI 图文"
    )
    text = next(dimension for dimension in match["dimensions"] if dimension["label"] == "文本")
    assert text["score"] == (None if provider_fails else 82)
    assert ("未评估" if provider_fails else "大模型") in text["explanation"]
    if provider_fails:
        assert "HTTP 503" in text["explanation"]
        assert "未启用" not in text["explanation"]


def test_disabled_ai_makes_no_requests(tmp_path, item_repository, feature_repository):
    def handler(request):
        pytest.fail("禁用时不得调用供应商")

    matcher = MultimodalMatcher(
        Settings(_env_file=None, matching_ai_enabled=False), feature_repository,
        transport=httpx.MockTransport(handler),
    )
    assert matcher.assess(item_repository.get_by_id(1), [item_repository.get_by_id(2)]) == {}


def test_candidate_limit_and_weighted_score(tmp_path, item_repository, feature_repository):
    source = replace(item_repository.get_by_id(1), owner_id=123)
    # 添加另一条同校区拾物，让模型只处理规则排名第一的一条。
    item_repository._items[8] = replace(
        item_repository.get_by_id(2), id=8, category="箱包", title="黑色双肩包",
    )
    item_repository._items[2] = replace(item_repository.get_by_id(2), category="箱包")
    calls = []

    def handler(request):
        content = json.loads(request.content)["messages"][1]["content"]
        candidates = [json.loads(part["text"]) for part in content if part["type"] == "text"]
        candidates = [row for row in candidates if row["role"] == "candidate"]
        assert len(candidates) == 1
        calls.append(candidates[0]["id"])
        return completion([
            {"candidate_id": candidates[0]["id"], "score": 90, "explanation": "外观接近"},
        ])

    matcher = MultimodalMatcher(
        ai_settings(tmp_path, matching_ai_max_candidates=1), feature_repository,
        transport=httpx.MockTransport(handler),
    )
    service = MatchingService(feature_repository, item_repository, matcher)
    service.generate_for_item(source)
    assert calls == [8]
    rows, _, _ = feature_repository.list_matches(recipient_id=123, offset=0, limit=10)
    ai_row = next(row for row in rows if row.candidate_item_id == 8)
    assessment = matcher.assess(source, [item_repository.get_by_id(8)])[8]
    rule_score = service._score(source, item_repository.get_by_id(8), assessment)[0]
    assert ai_row.score == round(rule_score * 0.4 + 90 * 0.6)
    unassessed = next(row for row in rows if row.candidate_item_id == 2)
    text = next(dimension for dimension in unassessed.dimensions if dimension["label"] == "文本")
    assert text["score"] is None
    assert "每次最多 1 条" in text["explanation"]


def test_ai_conflict_can_suppress_rule_match(tmp_path, item_repository, feature_repository):
    source = replace(item_repository.get_by_id(1), owner_id=123)
    item_repository._items[8] = replace(
        source, id=8, type=item_repository.get_by_id(2).type,
        owner_id=456,
    )
    matcher = MultimodalMatcher(
        ai_settings(tmp_path), feature_repository,
        transport=httpx.MockTransport(lambda request: completion([
            {"candidate_id": 8, "score": 0, "explanation": "图片中的配件明显不同"},
            {"candidate_id": 2, "score": 0, "explanation": "物品类别不符"},
        ])),
    )
    service = MatchingService(feature_repository, item_repository, matcher)
    assert service._score(source, item_repository.get_by_id(8))[0] >= 55
    service.generate_for_item(source)
    assert feature_repository.matches == {}


def test_enabled_ai_requires_complete_configuration():
    with pytest.raises(ValidationError, match="BASE_URL、API_KEY 和 MODEL"):
        Settings(_env_file=None, matching_ai_enabled=True, matching_ai_base_url=None)


def test_remote_plain_http_is_rejected():
    with pytest.raises(ValidationError, match="HTTPS"):
        Settings(_env_file=None, matching_ai_base_url="http://vision.example")


def test_semantic_text_score_replaces_characters_and_is_separate_from_image_score(
    tmp_path, item_repository, feature_repository,
):
    source = replace(
        item_repository.get_by_id(1), owner_id=123, location="北教1",
        title="黑色包包", description="黑色的" * 7,
    )
    candidate = replace(
        source, id=8, owner_id=456, type=item_repository.get_by_id(2).type,
        location="北教3", title="黑色双肩包", description="非常黑" * 9,
    )
    item_repository._items = {source.id: source, candidate.id: candidate}
    calls = []

    def handler(request):
        content = json.loads(request.content)["messages"][1]["content"]
        assert [part["type"] for part in content] == ["text", "text"]
        calls.append(request)
        return completion([{
            "candidate_id": candidate.id, "score": 20, "explanation": "没有图片证据",
            "text_score": 96, "text_explanation": "黑色包包与非常黑的双肩包语义接近",
        }])

    matcher = MultimodalMatcher(
        ai_settings(tmp_path, matching_ai_weight=0), feature_repository,
        transport=httpx.MockTransport(handler),
    )
    service = MatchingService(feature_repository, item_repository, matcher)
    service.generate_for_item(source)
    assert len(calls) == 1
    rows, total, _ = feature_repository.list_matches(recipient_id=123, offset=0, limit=10)
    assert total == 1
    text = next(dimension for dimension in rows[0].dimensions if dimension["label"] == "文本")
    assert text["score"] == 96  # 原共同字符比例只有38分，不再影响此分数。
    assert "语义接近" in text["explanation"]
    assert rows[0].dimensions[-1]["score"] == 20  # 不把图文分冒充文本分。
    assert rows[0].score == round(35 + 20 + 96 * .10 + 93 * .35)


@pytest.mark.parametrize("change", [
    {"text_score": 101}, {"text_score": -1}, {"text_score": "90"},
    {"text_explanation": ""}, {"text_score": None},
])
def test_invalid_semantic_score_is_not_used(tmp_path, item_repository, feature_repository, change):
    matcher = MultimodalMatcher(
        ai_settings(tmp_path), feature_repository,
        transport=httpx.MockTransport(lambda request: completion([
            {"candidate_id": 2, "score": 90, "explanation": "外观接近", **change},
        ])),
    )
    assert matcher.assess(item_repository.get_by_id(1), [item_repository.get_by_id(2)]) == {}


def test_missing_semantic_score_is_not_accepted(tmp_path, item_repository, feature_repository):
    old_response = json.dumps({"matches": [
        {"candidate_id": 2, "score": 90, "explanation": "旧格式只有图文分"},
    ]})
    matcher = MultimodalMatcher(
        ai_settings(tmp_path), feature_repository,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={
            "choices": [{"message": {"content": old_response}}],
        })),
    )
    assert matcher.assess(item_repository.get_by_id(1), [item_repository.get_by_id(2)]) == {}
    assert "评分格式" in matcher.failure_reason


def test_no_model_does_not_assign_text_score_even_for_identical_characters(item_repository):
    source = item_repository.get_by_id(1)
    score, dimensions = MatchingService._score(source, source)
    text = next(dimension for dimension in dimensions if dimension["label"] == "文本")
    assert text["score"] is None
    assert "未评估" in text["explanation"]
    assert score == 90  # 类别35+时间20+地点35，不补文本10分。
