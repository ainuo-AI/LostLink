"""图片上传、读取和删除接口。

上传与删除需要登录；只有已关联物品的图片可以通过公开地址读取，避免临时上传
在发布前被猜测访问。
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse, Response

from app.api.dependencies import get_current_user, get_media_service
from app.schemas.auth import UserRead
from app.schemas.feature import ImageRead
from app.services.feature_service import MediaService

router = APIRouter(prefix="/uploads/images", tags=["uploads"])


@router.post("", response_model=ImageRead, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: Annotated[UploadFile, File(description="JPG、PNG 或 WebP 图片")],
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[MediaService, Depends(get_media_service)],
) -> ImageRead:
    """读取受限大小的上传内容并交给 Service 校验和保存。"""

    data = await file.read(service.max_bytes + 1)
    return service.upload(
        data=data,
        content_type=(file.content_type or "").lower(),
        original_name=file.filename or "image",
        user=user,
    )


@router.get("/{image_id}", response_class=FileResponse)
def read_image(
    image_id: str,
    service: Annotated[MediaService, Depends(get_media_service)],
) -> FileResponse:
    """返回已关联物品的图片文件。"""

    path, content_type = service.locate(image_id)
    return FileResponse(path, media_type=content_type)


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    image_id: str,
    user: Annotated[UserRead, Depends(get_current_user)],
    service: Annotated[MediaService, Depends(get_media_service)],
) -> Response:
    """删除当前用户尚未关联到物品的临时图片。"""

    service.delete(image_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
