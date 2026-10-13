# 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
"""公开的校园地点选项，使用距离匹配的同一份目录。"""

from fastapi import APIRouter

from app.schemas.item import CampusLocationOption
from app.services.campus_distance import campus_distance_table

router = APIRouter(prefix="/locations", tags=["locations"])


# 文档对应：图2-2-2、图2-2-3 地点选择的接口支撑；2.2.10节GET /api/v1/locations。
@router.get("", response_model=list[CampusLocationOption], summary="读取校园地点选项")
def list_locations() -> list[CampusLocationOption]:
    return [
        CampusLocationOption(
            id=place["id"], name=place["name"], campus=place["campus"], area=place["area"],
            simulated=place["status"] == "synthetic",
        )
        for place in campus_distance_table().selectable_places()
    ]
