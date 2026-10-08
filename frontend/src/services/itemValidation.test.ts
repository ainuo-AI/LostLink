import { describe, expect, it } from 'vitest'
import { emptyDraft, maskContact, validateDraft, validateImages } from './itemValidation'
import type { CampusLocationOption } from './campusLocations'

const locations: CampusLocationOption[] = [
  { id: 'north', name: '图书馆', campus: '东丽校区', area: '北区', simulated: true },
  { id: 'south', name: '明德馆', campus: '东丽校区', area: '南区', simulated: false },
  { id: 'ninghe', name: '操场南门', campus: '宁河校区', area: null, simulated: true },
]
const now = new Date('2026-10-02T12:00:00')

function validDraft() {
  return {
    ...emptyDraft(),
    title: '黑色双肩包', category: '箱包' as const, campus: '东丽校区' as const,
    area: '北区' as const, location: '图书馆', occurredAt: '2026-09-29T12:00',
    description: '黑色背包上有一枚白色小熊徽章。', contact: '13800138000',
    storageMethod: 'office' as const, storageLocation: '明德馆', contactWindow: '工作日下午可联系',
  }
}

describe('物品表单校验', () => {
  it('有效的地点选项通过校验，宁河不需要区域', () => {
    expect(validateDraft(validDraft(), 'found', now, locations)).toEqual({})
    expect(validateDraft({ ...validDraft(), campus: '宁河校区', area: '',
      location: '操场南门', storageLocation: '操场南门' }, 'found', now, locations)).toEqual({})
  })

  it('拒绝自由文本、错误区域和跨校区保管地点', () => {
    const draft = { ...validDraft(), location: '图书馆二层', storageLocation: '操场南门' }
    const errors = validateDraft(draft, 'found', now, locations)
    expect(errors.location).toBeDefined()
    expect(errors.storageLocation).toBeDefined()
    expect(validateDraft({ ...validDraft(), area: '南区' }, 'lost', now, locations).location).toBeDefined()
  })

  it('拒绝首尾空格、未来时间和无效联系方式', () => {
    const draft = { ...validDraft(), title: '  ', contact: 'abc', occurredAt: '2026-10-03T12:00' }
    const errors = validateDraft(draft, 'lost', new Date('2026-10-02T12:00:00'))
    expect(errors.title).toBeDefined()
    expect(errors.contact).toBeDefined()
    expect(errors.occurredAt).toBeDefined()
  })

  it('拾物要求保管地点及联系范围，宁河校区不要求区域', () => {
    const draft = { ...validDraft(), campus: '宁河校区' as const, area: '' as const, storageLocation: '', contactWindow: '' }
    const errors = validateDraft(draft, 'found', new Date('2026-10-02T12:00:00'))
    expect(errors.area).toBeUndefined()
    expect(errors.storageLocation).toBeDefined()
    expect(errors.contactWindow).toBeDefined()
  })

  it('验证图片数量、格式与大小', () => {
    const png = new File(['x'], 'photo.png', { type: 'image/png' })
    const wrong = new File(['x'], 'photo.gif', { type: 'image/gif' })
    const huge = new File([new Uint8Array(5 * 1024 * 1024 + 1)], 'huge.jpg', { type: 'image/jpeg' })
    expect(validateImages([png], 2)).toBeNull()
    expect(validateImages([png, png], 2)).toContain('最多')
    expect(validateImages([wrong], 0)).toContain('仅支持')
    expect(validateImages([huge], 0)).toContain('5MB')
  })

  it('公开摘要中的联系方式脱敏', () => {
    expect(maskContact('13800138000')).toBe('138****8000')
    expect(maskContact('student@example.com')).toBe('s***@example.com')
  })
})
