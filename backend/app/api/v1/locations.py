"""公开的校园地点选项，使用距离匹配的同一份目录。"""

from fastapi import APIRouter

from app.schemas.item import CampusLocationOption
from app.services.campus_distance import campus_distance_table

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[CampusLocationOption], summary="读取校园地点选项")
def list_locations() -> list[CampusLocationOption]:
    return [
        CampusLocationOption(
            id=place["id"], name=place["name"], campus=place["campus"], area=place["area"],
            simulated=place["status"] == "synthetic",
        )
        for place in campus_distance_table().selectable_places()
    ]
