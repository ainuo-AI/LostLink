/** 纯前端举报存储测试。 */

import { afterEach, describe, expect, it, vi } from 'vitest'
import { createLocalReport } from './reports'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('createLocalReport', () => {
  it('把举报保存到浏览器并生成待处理编号', async () => {
    const values = new Map<string, string>()
    vi.stubGlobal('window', {
      localStorage: {
        getItem: (key: string) => values.get(key) ?? null,
        setItem: (key: string, value: string) => values.set(key, value),
      },
    })

    const report = await createLocalReport({
      item_id: 3,
      reason: 'inaccurate',
      description: '地点信息与实际情况不符，请管理员核实。',
    })

    expect(report.id).toBe(1)
    expect(report.status).toBe('pending')
    expect(JSON.parse(values.get('lostlink:reports') ?? '[]')).toHaveLength(1)
  })
})
