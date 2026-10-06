/** 举报 API 适配测试。 */

import { afterEach, describe, expect, it, vi } from 'vitest'
import { createLocalReport } from './reports'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('createLocalReport', () => {
  it('把物品编号放入路径并提交举报内容', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      id: 41, item_id: 3, reporter_id: 9, reason: 'inaccurate',
      description: '地点信息与实际情况不符，请管理员核实。',
      status: 'pending', created_at: '2026-10-06T00:00:00Z',
    }), { status: 201, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)

    const report = await createLocalReport({
      item_id: 3,
      reason: 'inaccurate',
      description: '地点信息与实际情况不符，请管理员核实。',
    })

    expect(report.id).toBe(41)
    expect(report.status).toBe('pending')
    const [url, init] = fetchMock.mock.calls[0]
    expect(new URL(url).pathname).toBe('/api/v1/items/3/reports')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body)).toEqual({
      reason: 'inaccurate',
      description: '地点信息与实际情况不符，请管理员核实。',
    })
  })
})
