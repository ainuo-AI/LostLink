/** 详情页与举报页的数据加载，始终以服务端最新公开详情为准。 */

import { fetchItem, toLostFoundItem } from '../api/items'
import type { LostFoundItem } from '../types/item'

/** 功能对应：读取单条详情，避免旧缓存或首页状态筛选影响已完成记录的展示。 */
export async function loadItemForPage(
  itemId: number,
  signal?: AbortSignal,
): Promise<LostFoundItem | null> {
  return toLostFoundItem(await fetchItem(itemId, signal))
}
