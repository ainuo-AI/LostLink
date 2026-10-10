"""离线地点识别、真实坐标距离表和匹配排序的回归验证。"""

import json
from dataclasses import replace

import pytest

from app.schemas.item import Campus, CampusArea
from app.services.campus_distance import (
    DATA_PATH,
    CampusDistanceTable,
    campus_distance_table,
    distance_similarity,
    straight_line_meters,
)
from app.services.feature_service import MatchingService
from scripts.build_campus_distances import build_matrix
from tests.api.test_item_management import authenticated_headers, lost_payload
from tests.api.test_remaining_features import found_payload


def test_saved_matrix_is_complete_symmetric_and_reproducible():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    assert data["distances_meters"] == build_matrix(data["places"])
    ids = {place["id"] for place in data["places"]}
    assert len(ids) == len(data["places"])
    assert set(data["distances_meters"]) == ids
    for place in data["places"]:
        row = data["distances_meters"][place["id"]]
        assert set(row) == ids
        if place["coordinates"] is not None:
            if place["status"] == "synthetic":
                assert place["source"]["kind"] == "synthetic"
                assert "url" not in place["source"]
            else:
                assert place["source"]["url"].startswith("https://www.openstreetmap.org/")
            assert row[place["id"]] == 0
        else:
            assert all(distance is None for distance in row.values())
        for other, distance in row.items():
            assert distance == data["distances_meters"][other][place["id"]]


def test_distance_units_and_decay():
    assert straight_line_meters(
        {"latitude": 0, "longitude": 0}, {"latitude": 1, "longitude": 0}
    ) == pytest.approx(111195, abs=1)
    assert [distance_similarity(distance) for distance in (0, 500, 1000, 2000, 3000)] == [
        100, 50, 25, 6, 0,
    ]
    with pytest.raises(ValueError):
        distance_similarity(-1)


@pytest.mark.parametrize("text", [
    "北教一", "北教1二层", "北教１ ３０２", "北教1号楼三层阅览区",
    "中国民航大学东丽校区北区北教一",
])
def test_aliases_floors_and_full_width_text_share_a_building(item_repository, text):
    item = replace(item_repository.get_by_id(1), location=text)
    other = replace(item, location="北教1")
    assessment = campus_distance_table().assess(item, other)
    assert assessment.distance_meters == 0
    assert assessment.score == 100
    assert "非步行路线" in assessment.explanation


@pytest.mark.parametrize("text", ["北教12", "北教一到北教二", "北教1附近不知何处", "测试地点"])
def test_unknown_or_ambiguous_text_is_not_a_near_match(item_repository, text):
    item = replace(item_repository.get_by_id(1), location=text)
    assert campus_distance_table().assess(item, item).score is None


def test_seed_locations_have_simulated_distances_except_test_placeholders(item_repository):
    table = campus_distance_table()
    for item in item_repository._items.values():
        place = table.resolve(item)
        assert place is not None
        assessment = table.assess(item, item)
        if place["status"] == "placeholder":
            assert assessment.distance_meters is None
        else:
            assert place["status"] == "synthetic"
            assert assessment.distance_meters == 0
            assert assessment.score == 100
            assert "模拟" in assessment.explanation
            assert "不代表实地距离" in assessment.explanation


def test_mixed_map_and_simulated_distance_is_labeled_in_both_directions(item_repository):
    source = item_repository.get_by_id(1)
    mapped = replace(source, location="北教一")
    forward = campus_distance_table().assess(source, mapped)
    reverse = campus_distance_table().assess(mapped, source)
    assert forward.distance_meters == reverse.distance_meters
    assert forward.distance_meters > 0
    assert forward.score == reverse.score
    for assessment in (forward, reverse):
        assert "包含模拟坐标" in assessment.explanation
        assert "不代表实地距离" in assessment.explanation


def test_campus_and_area_are_part_of_place_identity(item_repository):
    original = replace(item_repository.get_by_id(1), location="北教一")
    for changed in (
        replace(original, area=CampusArea.SOUTH),
        replace(original, campus=Campus.NINGHE, area=None),
    ):
        assert campus_distance_table().resolve(changed) is None


def test_duplicate_alias_does_not_silently_pick_first_place(item_repository):
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    data["places"][1]["aliases"].append("北教一")
    table = CampusDistanceTable(data)
    assert table.resolve(replace(item_repository.get_by_id(1), location="北教一")) is None


def test_real_distance_changes_ranking_with_same_other_features(item_repository):
    source = replace(item_repository.get_by_id(1), location="北教一")
    near = replace(source, id=100, location="北教三")
    far = replace(source, id=101, location="明德馆", area=CampusArea.SOUTH)
    near_score, near_dimensions = MatchingService._score(source, near)
    far_score, far_dimensions = MatchingService._score(source, far)
    assert near_score > far_score
    assert near_dimensions[-1]["label"] == "地点"
    assert "约 50 米" in near_dimensions[-1]["explanation"]
    assert "约 1231 米" in far_dimensions[-1]["explanation"]
    assert "模拟" not in near_dimensions[-1]["explanation"]
    assert near_dimensions[-1]["score"] > far_dimensions[-1]["score"]


def test_missing_coordinates_do_not_receive_geographic_bonus(item_repository):
    source = replace(item_repository.get_by_id(1), location="未登记建筑")
    score, dimensions = MatchingService._score(source, source)
    assert score == 55  # 类别35%+时间20%；缺少坐标和模型文本分时不补分。
    assert dimensions[-1]["score"] is None
    assert "未能唯一定位" in dimensions[-1]["explanation"]


def test_cross_campus_distance_is_not_confused_with_same_named_gate(item_repository):
    source = replace(item_repository.get_by_id(1), location="明德馆", area=CampusArea.SOUTH)
    other = replace(source, campus=Campus.NINGHE, area=None, location="南门")
    assessment = campus_distance_table().assess(source, other)
    assert assessment.distance_meters == 19323
    assert assessment.score == 0


@pytest.mark.parametrize("lost_location,found_location,score,meters,simulated", [
    ("北教1", "北教2", 89, 87, False),
    ("图书馆", "博学楼", 94, 47, True),
])
def test_published_match_explains_distance_in_api_response(
    client, lost_location, found_location, score, meters, simulated,
):
    lost_headers, _ = authenticated_headers(client, "distance-lost")
    found_headers, _ = authenticated_headers(client, "distance-found")
    lost = client.post(
        "/api/v1/items", headers=lost_headers, json=lost_payload(location=lost_location)
    )
    found = client.post(
        "/api/v1/items", headers=found_headers, json=found_payload(location=found_location)
    )
    assert lost.status_code == found.status_code == 201
    notifications = client.get("/api/v1/notifications", headers=lost_headers).json()["items"]
    match = next(row for row in notifications if row["candidate"]["id"] == found.json()["id"])
    location = next(dimension for dimension in match["dimensions"] if dimension["label"] == "地点")
    assert location["score"] == score
    assert f"约 {meters} 米" in location["explanation"]
    assert ("模拟" in location["explanation"]) is simulated
