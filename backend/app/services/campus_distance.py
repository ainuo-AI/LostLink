"""读取离线校园距离矩阵；匹配过程不调用地图接口。"""

import json
import math
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.repositories.item_repository import ItemRecord

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "campus_distances.json"
# 500 米时为 50 分，1500 米时为 12 分；超过 3 公里不提供地点相似度。
HALF_DISTANCE_METERS = 500
MAX_DISTANCE_METERS = 3000


def normalize_location(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value)).casefold()


def straight_line_meters(first: dict, second: dict) -> int:
    """同一 WGS84 坐标系的球面距离，取整到米。"""

    lat1, lat2 = math.radians(first["latitude"]), math.radians(second["latitude"])
    dlat = lat2 - lat1
    dlon = math.radians(second["longitude"] - first["longitude"])
    term = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return round(6371008.8 * 2 * math.asin(math.sqrt(min(1, max(0, term)))))


def distance_similarity(distance_meters: int) -> int:
    if distance_meters < 0:
        raise ValueError("距离不能为负数")
    if distance_meters >= MAX_DISTANCE_METERS:
        return 0
    return round(100 * 2 ** (-distance_meters / HALF_DISTANCE_METERS))


@dataclass(frozen=True)
class LocationAssessment:
    score: int | None
    distance_meters: int | None
    explanation: str


class CampusDistanceTable:
    def __init__(self, data: dict) -> None:
        if data["coordinate_system"] != "WGS84" or data["distance_kind"] != "straight_line":
            raise ValueError("校园距离表必须使用 WGS84 直线距离")
        self.places = data["places"]
        self.distances = data["distances_meters"]

    def selectable_places(self) -> list[dict]:
        """只公开有坐标的业务地点，不把开发占位项作为用户选项。"""

        return [place for place in self.places if place["coordinates"] is not None]

    def is_selection(self, campus, area, name, *, any_area: bool = False) -> bool:
        return any(
            place["campus"] == campus
            and (any_area or place["area"] == area)
            and place["name"] == name
            for place in self.selectable_places()
        )

    def resolve(self, item: ItemRecord) -> dict | None:
        text = normalize_location(item.location)
        for prefix in ["中国民航大学", item.campus.value, item.area.value if item.area else ""]:
            if prefix and text.startswith(prefix):
                text = text[len(prefix):].lstrip("·-:/")
        matches = []
        for place in self.places:
            if place["campus"] != item.campus or place["area"] != item.area:
                continue
            for alias in [place["name"], *place["aliases"]]:
                name = normalize_location(alias)
                # 只容许楼层、房间或馆内区域后缀，不能把北教12识别成北教1。
                suffix = text[len(name):] if text.startswith(name) else None
                if suffix is not None and (
                    not suffix or re.fullmatch(
                        r"(?:\d{3,4}(?:室)?|第?[一二三四五六七八九十百零〇\d]+"
                        r"(?:层|楼)(?:阅览区|阅览室|大厅|值班室|服务台)?|"
                        r"阅览区|阅览室|大厅|值班室|服务台|门口)", suffix
                    )
                ):
                    matches.append(place)
                    break
        return matches[0] if len(matches) == 1 else None

    def assess(self, source: ItemRecord, candidate: ItemRecord) -> LocationAssessment:
        first, second = self.resolve(source), self.resolve(candidate)
        if first is None or second is None:
            return LocationAssessment(None, None, "地点未能唯一定位，未评估距离相似度。")
        distance = self.distances[first["id"]][second["id"]]
        if distance is None:
            return LocationAssessment(
                None, None, "地点已收录，但地图坐标待核实，未评估距离相似度。"
            )
        simulated = first["status"] == "synthetic" or second["status"] == "synthetic"
        distance_label = "包含模拟坐标，模拟直线距离" if simulated else "地图建筑代表点直线距离"
        explanation = (
            f"{first['name']} ↔ {second['name']}：{distance_label}约 {distance} 米；"
            + ("仅用于演示，不代表实地距离。" if simulated else "")
            + "楼层和室内位置按同一建筑计算，非步行路线距离。"
        )
        return LocationAssessment(distance_similarity(distance), distance, explanation)


@lru_cache(maxsize=1)
def campus_distance_table() -> CampusDistanceTable:
    return CampusDistanceTable(json.loads(DATA_PATH.read_text(encoding="utf-8")))
