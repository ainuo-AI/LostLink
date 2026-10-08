"""从 WGS84 坐标离线生成两两距离（含明确标记的模拟坐标；缺坐标保留 null）。

在 backend 目录运行：.venv/bin/python -m scripts.build_campus_distances
仅更新 JSON 中的距离矩阵，不联网、不推测或补写坐标。
"""

import json

from app.services.campus_distance import DATA_PATH, straight_line_meters


def build_matrix(places: list[dict]) -> dict[str, dict[str, int | None]]:
    return {
        first["id"]: {
            second["id"]: (
                straight_line_meters(first["coordinates"], second["coordinates"])
                if first["coordinates"] is not None and second["coordinates"] is not None
                else None
            )
            for second in places
        }
        for first in places
    }


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    data["distances_meters"] = build_matrix(data["places"])
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mapped = sum(place["status"] == "map_verified" for place in data["places"])
    synthetic = sum(place["status"] == "synthetic" for place in data["places"])
    print(f"已重建距离矩阵：{mapped} 个地图地点，{synthetic} 个模拟地点；缺坐标项保留 null。")


if __name__ == "__main__":
    main()
