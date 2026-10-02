import { afterEach, describe, expect, it, vi } from 'vitest'
import { decideMatch, getMatchNotification, listMatchNotifications, markAllMatchesRead, markMatchRead } from './matches'

afterEach(() => vi.unstubAllGlobals())

function memoryStorage() {
  const values = new Map<string, string>()
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
  }
}

describe('本地匹配通知服务', () => {
  it('已读与处理状态独立，反馈后刷新仍保留原始模拟得分', async () => {
    vi.stubGlobal('window', { localStorage: memoryStorage() })
    const initial = await listMatchNotifications()
    const target = initial.find((item) => !item.read && item.status === 'pending')!
    expect(target.dimensions.find((item) => item.label === '图片')?.score).toBeNull()
    const score = target.score
    const dimensions = JSON.stringify(target.dimensions)
    await markMatchRead(target.id)
    expect((await getMatchNotification(target.id))?.status).toBe('pending')
    const decided = await decideMatch(target.id, 'rejected', '特征不符', '颜色不同')
    expect(decided.read).toBe(true)
    expect(decided.status).toBe('rejected')
    expect((await getMatchNotification(target.id))?.score).toBe(score)
    expect(JSON.stringify((await getMatchNotification(target.id))?.dimensions)).toBe(dimensions)
    await expect(decideMatch(target.id, 'confirmed')).rejects.toThrow('不能重复')
  })

  it('全部标为已读后不改变处理状态', async () => {
    vi.stubGlobal('window', { localStorage: memoryStorage() })
    const before = await listMatchNotifications()
    await markAllMatchesRead()
    const after = await listMatchNotifications()
    expect(after.every((item) => item.read)).toBe(true)
    expect(after.map((item) => item.status)).toEqual(before.map((item) => item.status))
  })

  it('本地数据损坏时明确报错，不自动覆盖用户数据', async () => {
    const values = memoryStorage()
    values.setItem('lostlink:demo:matches:v1', '{broken')
    vi.stubGlobal('window', { localStorage: values })
    await expect(listMatchNotifications()).rejects.toThrow('已损坏')
  })
})
