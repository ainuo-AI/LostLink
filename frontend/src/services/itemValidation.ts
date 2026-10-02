/**
 * 发布与登记表单的纯校验模块
 *
 * 这里不依赖 Vue 组件和浏览器存储，因此规则可以被页面与 Vitest 共同调用。
 * 后续接入真实接口时，后端仍需再次校验，前端校验不能代替服务端安全校验。
 */
import type { CampusArea } from '../types/item'
import { ITEM_CATEGORIES, type DraftErrors, type ItemDraft } from '../types/demo'

export const MAX_IMAGES = 3
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024
export const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']

/** 为失物和拾物表单创建字段完整、互不共享引用的空草稿。 */
export function emptyDraft(): ItemDraft {
  return {
    title: '', category: '', campus: '', area: '', location: '', occurredAt: '',
    description: '', contact: '', contactNote: '', storageMethod: '',
    storageLocation: '', contactWindow: '', imageIds: [],
  }
}

/**
 * 一次性返回“字段名 → 错误文案”，便于页面在对应输入框附近展示错误。
 * type 为 found 时额外检查保管方式、保管地点和可联系时间。
 */
export function validateDraft(draft: ItemDraft, type: 'lost' | 'found', now = new Date()): DraftErrors {
  const errors: DraftErrors = {}
  const trimmed = (value: string) => value.trim()
  const title = trimmed(draft.title)
  if (title.length < 2 || title.length > 60) errors.title = '物品名称需填写 2–60 个字。'
  if (!ITEM_CATEGORIES.includes(draft.category as typeof ITEM_CATEGORIES[number])) errors.category = '请选择物品类别。'
  if (draft.campus !== '东丽校区' && draft.campus !== '宁河校区') errors.campus = '请选择校区。'
  if (draft.campus === '东丽校区' && !(['北区', '南区'] as CampusArea[]).includes(draft.area as CampusArea)) errors.area = '请选择东丽校区区域。'
  if (trimmed(draft.location).length < 2 || trimmed(draft.location).length > 100) errors.location = '具体地点需填写 2–100 个字。'
  const occurredAt = new Date(draft.occurredAt)
  if (!draft.occurredAt || Number.isNaN(occurredAt.getTime())) errors.occurredAt = '请选择有效的日期和时间。'
  else if (occurredAt.getTime() > now.getTime()) errors.occurredAt = '时间不能晚于当前时间。'
  if (trimmed(draft.description).length < 10 || trimmed(draft.description).length > 500) errors.description = '特征描述需填写 10–500 个字。'
  const contact = trimmed(draft.contact)
  if (!/^1[3-9]\d{9}$/.test(contact) && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contact)) errors.contact = '请输入有效的中国大陆手机号或电子邮箱。'
  if (trimmed(draft.contactNote).length > 200) errors.contactNote = '联系说明不能超过 200 个字。'
  if (type === 'found') {
    if (draft.storageMethod !== 'self' && draft.storageMethod !== 'office') errors.storageMethod = '请选择保管方式。'
    if (trimmed(draft.storageLocation).length < 2 || trimmed(draft.storageLocation).length > 100) errors.storageLocation = '保管地点需填写 2–100 个字。'
    if (trimmed(draft.contactWindow).length < 2 || trimmed(draft.contactWindow).length > 100) errors.contactWindow = '请填写可联系时间或范围（2–100 个字）。'
  }
  if (draft.imageIds.length > MAX_IMAGES) errors.imageIds = '最多选择 3 张图片。'
  return errors
}

/** 图片规则单独校验，已有数量也计入最多 3 张的限制。 */
export function validateImages(files: File[], existingCount: number): string | null {
  if (files.length + existingCount > MAX_IMAGES) return `最多选择 ${MAX_IMAGES} 张图片。`
  if (files.some((file) => !IMAGE_TYPES.includes(file.type))) return '仅支持 JPG、PNG、WebP 图片。'
  if (files.some((file) => file.size > MAX_IMAGE_BYTES)) return '每张图片不能超过 5MB。'
  return null
}

/** 生成列表或摘要可使用的脱敏联系方式，不展示用户输入的完整手机号或邮箱名。 */
export function maskContact(value: string): string {
  const contact = value.trim()
  if (contact.includes('@')) {
    const [name, domain] = contact.split('@')
    return `${name.slice(0, 1)}***@${domain}`
  }
  return `${contact.slice(0, 3)}****${contact.slice(-4)}`
}
