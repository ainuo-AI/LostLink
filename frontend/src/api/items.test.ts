/** 失物与拾物 API 客户端测试。 */

import { afterEach, describe, expect, it, vi } from 'vitest'
import { fetchItems, formatDisplayTime, toLostFoundItem } from './items'
import type { ApiItem } from '../types/item'

const apiItem: ApiItem = {
  id: 3,
  type: 'found',
  category: '数码',
  title: '白色无线耳机',
  description: '白色充电仓',
  location: '操场南门',
  campus: '宁河校区',
  area: null,
  occurred_at: '2026-09-30T08:30:00Z',
  status: 'active',
  contact_hint: '请描述蓝牙名称。',
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('fetchItems', () => {
  it('将页面筛选条件转换为后端查询参数', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      items: [apiItem],
      page: 1,
      page_size: 6,
      total: 1,
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchItems({
      keyword: '耳机',
      type: 'found',
      campus: '宁河校区',
      days: 30,
      page: 1,
      pageSize: 6,
    })

    const requestedUrl = new URL(fetchMock.mock.calls[0][0])
    expect(requestedUrl.pathname).toBe('/api/v1/items')
    expect(requestedUrl.searchParams.get('keyword')).toBe('耳机')
    expect(requestedUrl.searchParams.get('type')).toBe('found')
    expect(requestedUrl.searchParams.get('campus')).toBe('宁河校区')
    expect(requestedUrl.searchParams.get('days')).toBe('30')
    expect(result.total).toBe(1)
  })

  it('将后端统一错误转换为 ApiError', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      code: 'DATABASE_UNAVAILABLE',
      message: '数据服务暂时不可用，请稍后重试',
      details: null,
      request_id: 'request-1',
    }), { status: 503, headers: { 'Content-Type': 'application/json' } })))

    await expect(fetchItems({ page: 1, pageSize: 6 })).rejects.toMatchObject({
      status: 503,
      code: 'DATABASE_UNAVAILABLE',
      requestId: 'request-1',
    })
  })
})

describe('item display adapter', () => {
  it('把 API 字段转换为卡片展示字段', () => {
    const item = toLostFoundItem(apiItem)

    expect(item.area).toBe('')
    expect(item.contactHint).toBe('请描述蓝牙名称。')
    expect(item.icon).toBe('🎧')
    expect(item.occurredAt).toBe(apiItem.occurred_at)
  })

  it('为当天和无效时间生成明确文案', () => {
    expect(formatDisplayTime('2026-09-30T08:30:00Z', new Date('2026-09-30T12:00:00Z')))
      .toContain('今天')
    expect(formatDisplayTime('not-a-date')).toBe('时间未知')
  })
})
