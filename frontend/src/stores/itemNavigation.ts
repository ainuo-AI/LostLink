/** 详情页导航数据。
 *
 * 当前后端只有列表查询接口，所以先缓存用户刚点击的卡片；若页面刷新导致缓存缺失，
 * 再调用现有列表接口查找。以后后端增加 GET /items/{id} 时，只需替换本模块。
 */

import { fetchItems, toLostFoundItem } from '../api/items'
import type { LostFoundItem } from '../types/item'

const SELECTED_ITEM_KEY = 'lostlink:selected-item'

/** 功能对应：首页点击卡片时保存当前公开数据，供详情页立即展示。 */
export function cacheItemForNavigation(item: LostFoundItem): void {
  try {
    window.sessionStorage.setItem(SELECTED_ITEM_KEY, JSON.stringify(item))
  } catch {
    // 浏览器禁用存储时仍允许路由跳转，详情页会改走列表接口兜底。
  }
}

function readCachedItem(itemId: number): LostFoundItem | null {
  // sessionStorage 只缓存最近点击的公开卡片数据，关闭标签页后自动消失。
  try {
    const raw = window.sessionStorage.getItem(SELECTED_ITEM_KEY)
    if (!raw) return null
    const item = JSON.parse(raw) as LostFoundItem
    return item.id === itemId ? item : null
  } catch {
    return null
  }
}

/** 功能对应：为详情页和举报页提供物品数据，全程只使用现有前端列表 API。 */
export async function loadItemForPage(
  itemId: number,
  signal?: AbortSignal,
): Promise<LostFoundItem | null> {
  const cached = readCachedItem(itemId)
  if (cached) return cached

  // 刷新后内存和 session 缓存可能缺失，临时从现有列表接口最多查 100 条兜底。
  // 这不是正式的单条详情查询；后端增加 GET /items/{id} 后应替换这里。
  const response = await fetchItems({ page: 1, pageSize: 100 }, signal)
  const found = response.items.find((item) => item.id === itemId)
  return found ? toLostFoundItem(found) : null
}
