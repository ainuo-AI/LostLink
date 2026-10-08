import { afterEach, describe, expect, it, vi } from 'vitest'
import { isLocationSelection, locationOptions, useCampusLocations, type CampusLocationOption } from './campusLocations'

const locations: CampusLocationOption[] = [
  { id: 'north', name: '图书馆', campus: '东丽校区', area: '北区', simulated: true },
  { id: 'south', name: '明德馆', campus: '东丽校区', area: '南区', simulated: false },
  { id: 'ninghe', name: '操场南门', campus: '宁河校区', area: null, simulated: true },
]

afterEach(() => vi.unstubAllGlobals())

describe('校园地点选项', () => {
  it('发生地点按校区和区域筛选，保管地点允许同校区跨区域', () => {
    expect(locationOptions(locations, '', '')).toEqual([])
    expect(locationOptions(locations, '东丽校区', '')).toEqual([])
    expect(locationOptions(locations, '东丽校区', '北区')).toEqual([locations[0]])
    expect(locationOptions(locations, '东丽校区', '南区')).toEqual([locations[1]])
    expect(locationOptions(locations, '宁河校区', null)).toEqual([locations[2]])
    expect(locationOptions(locations, '东丽校区', null, true)).toEqual(locations.slice(0, 2))
  })

  it('只能提交选项原名，不接受别名、楼层或其他校区地点', () => {
    expect(isLocationSelection(locations, '东丽校区', '北区', '图书馆')).toBe(true)
    for (const name of ['图书馆二层', '未知地点', '明德馆', '操场南门']) {
      expect(isLocationSelection(locations, '东丽校区', '北区', name)).toBe(false)
    }
  })

  it('加载失败后可重试，选项直接来自后端', async () => {
    const fetchMock = vi.fn().mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce(new Response(JSON.stringify(locations)))
    vi.stubGlobal('fetch', fetchMock)
    const catalog = useCampusLocations()
    await catalog.load()
    expect(catalog.loading.value).toBe(false)
    expect(catalog.error.value).toContain('重试')
    expect(catalog.choices.value).toEqual([])
    await catalog.load()
    expect(catalog.error.value).toBe('')
    expect(catalog.choices.value).toEqual(locations)
    expect(new URL(fetchMock.mock.calls[1]![0]).pathname).toBe('/api/v1/locations')
  })
})
