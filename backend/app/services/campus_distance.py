# 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
# 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
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


# 文档对应：图2-2-10 地点评分的直线距离计算；2.2.10节匹配计算规则。
def straight_line_meters(first: dict, second: dict) -> int:
    """同一 WGS84 坐标系的球面距离，取整到米。"""

    lat1, lat2 = math.radians(first["latitude"]), math.radians(second["latitude"])
    dlat = lat2 - lat1
    dlon = math.radians(second["longitude"] - first["longitude"])
    term = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return round(6371008.8 * 2 * math.asin(math.sqrt(min(1, max(0, term)))))


# 文档对应：图2-2-10 地点相似度：500米为50分，3000米及以上为0分。
# 设计文档对应：图4-1-7 使用米数计算地点分，3000 米及以上取 0。
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


# 文档对应：图2-2-10 地点评分的离线目录与距离矩阵；2.3节辅助数据。
# 设计文档对应：图2-1、图4-2 CampusDistanceTable 的职责与成员关系。
class CampusDistanceTable:
    def __init__(self, data: dict) -> None:
        if data["coordinate_system"] != "WGS84" or data["distance_kind"] != "straight_line":
            raise ValueError("校园距离表必须使用 WGS84 直线距离")
        self.places = data["places"]
        self.distances = data["distances_meters"]

    # 文档对应：图2-2-2、图2-2-3 地点下拉选项的目录支撑；2.2.10节排除无坐标占位项。
    # 设计文档对应：图3-2-4、图3-2-7 只返回有坐标的公开目录地点。
    def selectable_places(self) -> list[dict]:
        """只公开有坐标的业务地点，不把开发占位项作为用户选项。"""

        return [place for place in self.places if place["coordinates"] is not None]

    # 文档对应：图2-2-2、图2-2-3、图2-2-5 的标准地点与校区、区域校验。
    # 设计文档对应：图3-2-4、图3-2-7 按校区、区域和标准名称校验地点；保管地点允许同校区跨区域。
    def is_selection(self, campus, area, name, *, any_area: bool = False) -> bool:
        return any(
            place["campus"] == campus
            and (any_area or place["area"] == area)
            and place["name"] == name
            for place in self.selectable_places()
        )

    # 文档对应：图2-2-10 识别已有线索的地点别名和楼层；无法唯一定位时不评分。
    # 设计文档对应：图4-1-7、图4-2 唯一解析候选地点，无法定位时保留未评估状态。
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

    # 文档对应：图2-2-10 读取米制距离并计算地点分；缺坐标与模拟地点说明见2.2.10节。
    # 设计文档对应：图4-1-7 从离线距离矩阵读取米数、相似度与距离说明。
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


# 设计文档对应：图4-4、表4-1、图4-3 缓存读取本地 campus_distances.json，地点与距离使用 JSON 保存。
@lru_cache(maxsize=1)
# 文档对应：图2-2-10 读取并缓存离线距离矩阵；坐标更新后的重建要求见2.2.10节。
def campus_distance_table() -> CampusDistanceTable:
    return CampusDistanceTable(json.loads(DATA_PATH.read_text(encoding="utf-8")))
