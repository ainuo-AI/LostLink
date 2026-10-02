import { describe, expect, it } from 'vitest'
import { emptyDraft, maskContact, validateDraft, validateImages } from './itemValidation'

function validDraft() {
  return {
    ...emptyDraft(),
    title: '黑色双肩包', category: '箱包' as const, campus: '东丽校区' as const,
    area: '北区' as const, location: '图书馆二层', occurredAt: '2026-09-29T12:00',
    description: '黑色背包上有一枚白色小熊徽章。', contact: '13800138000',
    storageMethod: 'office' as const, storageLocation: '教学楼值班室', contactWindow: '工作日下午可联系',
  }
}

describe('物品表单校验', () => {
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
