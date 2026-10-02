import { afterEach, describe, expect, it, vi } from 'vitest'
import { emptyDraft } from './itemValidation'
import { loadDraft, publishLocalItem, saveDraft } from './localItems'

afterEach(() => vi.unstubAllGlobals())

function memoryStorage(failWrite = false) {
  const values = new Map<string, string>()
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => { if (failWrite) throw new Error('quota'); values.set(key, value) },
    removeItem: (key: string) => values.delete(key),
  }
}

describe('本地发布服务', () => {
  it('失物和拾物草稿隔离，发布后只保存脱敏联系方式', async () => {
    vi.stubGlobal('window', { localStorage: memoryStorage() })
    const lost = { ...emptyDraft(), title: '黑色双肩包' }
    await saveDraft('lost', lost)
    expect((await loadDraft('lost'))?.title).toBe('黑色双肩包')
    expect(await loadDraft('found')).toBeNull()
    const record = await publishLocalItem('lost', {
      ...lost, category: '箱包', campus: '宁河校区', location: '图书馆',
      occurredAt: '2026-09-30T10:00', description: '黑色背包有白色小熊徽章。', contact: '13800138000',
    })
    expect(record.id).toMatch(/^demo-lost-/)
    expect(record.contactMasked).toBe('138****8000')
    expect(JSON.stringify(record)).not.toContain('13800138000')
  })

  it('存储写入失败时不返回成功记录', async () => {
    vi.stubGlobal('window', { localStorage: memoryStorage(true) })
    await expect(publishLocalItem('found', { ...emptyDraft(), category: '书籍', occurredAt: '2026-09-30T10:00' })).rejects.toThrow('本地存储')
  })
})
