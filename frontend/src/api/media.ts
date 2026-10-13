// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
/** 图片上传与临时文件清理 API。 */

import { requestJson } from './client'

export interface UploadedImage {
  id: string
  content_type: string
  size_bytes: number
  url: string
  created_at: string
}

/** 发布物品前把 IndexedDB 中的本地图片上传到服务端。 */
// 文档对应：图2-2-2、图2-2-3 提交前上传图片；3.1节；2.2节用例业务规则 图片边界。
export function uploadImage(blob: Blob, filename: string): Promise<UploadedImage> {
  const form = new FormData()
  form.append('file', blob, filename)
  return requestJson<UploadedImage>('/api/v1/uploads/images', {
    method: 'POST',
    body: form,
  }, { authenticated: true })
}

/** 发布失败时删除已上传但尚未关联的临时图片。 */
// 文档对应：图2-2-2、图2-2-3 发布失败时清理临时上传。
export function deleteUploadedImage(imageId: string): Promise<void> {
  return requestJson<void>(`/api/v1/uploads/images/${imageId}`, {
    method: 'DELETE',
  }, { authenticated: true })
}
