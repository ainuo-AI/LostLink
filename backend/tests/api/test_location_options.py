"""地点目录、校区范围与禁止自由文本的 API 契约。"""

import pytest

from tests.api.test_item_management import authenticated_headers, lost_payload
from tests.api.test_remaining_features import found_payload


def test_public_catalog_only_contains_selectable_locations(client):
    response = client.get("/api/v1/locations")
    assert response.status_code == 200
    places = response.json()
    assert len(places) == 21
    assert len({place["id"] for place in places}) == 21
    assert sum(place["simulated"] for place in places) == 6
    assert {place["name"] for place in places}.isdisjoint({"测试地点", "演示地点"})
    assert all(set(place) == {"id", "name", "campus", "area", "simulated"} for place in places)


@pytest.mark.parametrize("changes", [
    {"location": "任意教学楼"},
    {"location": "图书馆二层"},
    {"location": "北教一"},
    {"location": "明德馆"},
    {"location": "操场南门"},
    {"location": "演示地点"},
])
def test_create_rejects_text_aliases_and_wrong_location_scope(client, changes):
    headers, _ = authenticated_headers(client)
    response = client.post("/api/v1/items", headers=headers, json=lost_payload(**changes))
    assert response.status_code == 422
    assert response.json()["code"] == "ITEM_LOCATION_INVALID"
    assert client.get("/api/v1/users/me/items", headers=headers).json()["total"] == 0


def test_all_catalog_options_can_be_published(client):
    headers, _ = authenticated_headers(client)
    for place in client.get("/api/v1/locations").json():
        response = client.post("/api/v1/items", headers=headers, json=lost_payload(
            campus=place["campus"], area=place["area"], location=place["name"],
        ))
        assert response.status_code == 201, place
        assert response.json()["location"] == place["name"]


@pytest.mark.parametrize("storage,expected", [
    ("明德馆", 201),  # 同一校区允许跨区域保管。
    ("图书馆值班室", 422),
    ("操场南门", 422),
])
def test_storage_location_must_be_a_selection_in_the_same_campus(client, storage, expected):
    headers, _ = authenticated_headers(client)
    response = client.post(
        "/api/v1/items", headers=headers, json=found_payload(storage_location=storage)
    )
    assert response.status_code == expected
    if expected == 422:
        assert response.json()["code"] == "ITEM_LOCATION_INVALID"


def test_partial_updates_validate_final_location_and_storage_scope(client):
    headers, _ = authenticated_headers(client)
    created = client.post("/api/v1/items", headers=headers, json=found_payload()).json()
    url = f"/api/v1/items/{created['id']}"
    for changes in [
        {"location": "图书馆三层"},
        {"area": "南区"},
        {"storage_location": "操场南门"},
        {"campus": "宁河校区", "area": None, "location": "操场南门"},
    ]:
        rejected = client.patch(url, headers=headers, json=changes)
        assert rejected.status_code == 422
        assert rejected.json()["code"] == "ITEM_LOCATION_INVALID"
    assert client.get(url).json()["location"] == "图书馆"
    updated = client.patch(url, headers=headers, json={
        "campus": "宁河校区", "area": None, "location": "操场南门",
        "storage_location": "第二食堂",
    })
    assert updated.status_code == 200
    assert updated.json()["storage_location"] == "第二食堂"
