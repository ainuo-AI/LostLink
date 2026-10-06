/** 匹配通知 API 适配测试。 */

import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  decideMatch,
  getMatchNotification,
  listMatchNotifications,
  markAllMatchesRead,
  markMatchRead,
} from './matches'

const item = {
  id: 1, type: 'lost', category: '数码', title: '无线耳机', description: '黑色耳机盒',
  location: '图书馆', campus: '东丽校区', area: '北区', occurred_at: '2026-10-01T00:00:00Z',
  status: 'active', contact_hint: '请核验特征', image_urls: [],
}

function apiMatch(id = 8, read = false, status = 'pending') {
  return {
    id, title: '发现候选', summary: '请核对', created_at: '2026-10-06T00:00:00Z',
    is_read: read, status, mine: item, candidate: { ...item, id: 2, type: 'found' }, score: 82,
    dimensions: [{ label: '类别', score: 100, explanation: '类别相同' }],
    rejection_reason: null as string | null, rejection_note: null as string | null,
  }
}

afterEach(() => vi.unstubAllGlobals())

describe('匹配通知 API', () => {
  it('读取列表、标记已读并提交拒绝反馈', async () => {
    let current = apiMatch()
    const fetchMock = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const path = new URL(String(input)).pathname
      if (path === '/api/v1/notifications') {
        return new Response(JSON.stringify({ items: [current], page: 1, page_size: 100, total: 1, unread: current.is_read ? 0 : 1 }))
      }
      if (path.endsWith('/read')) current = { ...current, is_read: true }
      if (path.endsWith('/feedback')) current = {
        ...current, is_read: true, status: 'rejected',
        rejection_reason: '特征不符', rejection_note: '颜色不同',
      }
      expect(init?.method === 'PATCH' || !init?.method).toBe(true)
      return new Response(JSON.stringify(current))
    })
    vi.stubGlobal('fetch', fetchMock)

    const listed = await listMatchNotifications()
    expect(listed[0].score).toBe(82)
    expect((await markMatchRead('8')).read).toBe(true)
    expect((await getMatchNotification('8'))?.status).toBe('pending')
    const rejected = await decideMatch('8', 'rejected', '特征不符', '颜色不同')
    expect(rejected.status).toBe('rejected')
    expect(rejected.rejectionReason).toBe('特征不符')
  })

  it('全部标为已读会逐条调用受保护更新接口', async () => {
    const matches = [apiMatch(1), apiMatch(2), apiMatch(3, true)]
    const fetchMock = vi.fn(async (input: string | URL | Request) => {
      const path = new URL(String(input)).pathname
      if (path === '/api/v1/notifications') {
        return new Response(JSON.stringify({ items: matches, page: 1, page_size: 100, total: 3, unread: 2 }))
      }
      const id = Number(path.split('/')[4])
      return new Response(JSON.stringify({ ...matches.find(item => item.id === id), is_read: true }))
    })
    vi.stubGlobal('fetch', fetchMock)

    await markAllMatchesRead()
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('无效编号不会发送请求', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    expect(await getMatchNotification('invalid')).toBeNull()
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
