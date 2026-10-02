/**
 * 发布与登记的前端模拟服务
 *
 * 它把页面与 localStorage 细节隔开：组件只调用 load/save/publish 方法。
 * 后续后端提供正式 API 时，可以替换本服务而尽量不改表单结构。
 */
import type { RecordType } from '../types/item'
import { ITEM_CATEGORIES, type ItemCategory, type ItemDraft, type LocalItemRecord } from '../types/demo'
import { maskContact } from './itemValidation'

const DRAFT_PREFIX = 'lostlink:demo:draft:'
const RECORDS_KEY = 'lostlink:demo:item-records:v1'

/** 下列类型守卫用于验证 localStorage 中的不可信 JSON，避免损坏数据进入页面。 */
function isObject(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function isItemDraft(value: unknown): value is ItemDraft {
  return isObject(value)
    && ['title', 'category', 'campus', 'area', 'location', 'occurredAt', 'description', 'contact', 'contactNote', 'storageMethod', 'storageLocation', 'contactWindow'].every((key) => typeof value[key] === 'string')
    && Array.isArray(value.imageIds) && value.imageIds.every((id: unknown) => typeof id === 'string')
}

function isLocalRecord(value: unknown): value is LocalItemRecord {
  return isObject(value)
    && ['id', 'title', 'category', 'campus', 'area', 'location', 'occurredAt', 'description', 'contactMasked', 'contactNote', 'createdAt'].every((key) => typeof value[key] === 'string')
    && (value.type === 'lost' || value.type === 'found')
    && value.status === 'pending-match'
    && Array.isArray(value.imageIds) && value.imageIds.every((id: unknown) => typeof id === 'string')
}

export class DemoStorageError extends Error {
  constructor(message = '浏览器本地存储不可用或空间不足，请检查设置后重试。') {
    super(message)
    this.name = 'DemoStorageError'
  }
}

/** 统一取得 localStorage，并把浏览器权限或容量异常转换为业务可读错误。 */
function getStorage(): Storage {
  try {
    return window.localStorage
  } catch {
    throw new DemoStorageError()
  }
}

/** 读取记录数组时执行结构校验；发现损坏数据时不自动覆盖用户现有内容。 */
function parseArray(raw: string | null): LocalItemRecord[] {
  if (!raw) return []
  try {
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed) || !parsed.every(isLocalRecord)) throw new Error('invalid records')
    return parsed
  } catch {
    throw new DemoStorageError('本地演示记录已损坏，请清理浏览器站点数据后重试。')
  }
}

/** 使用 lost/found 后缀读取草稿，因此切换两个页面时不会混用表单内容。 */
export async function loadDraft(type: RecordType): Promise<ItemDraft | null> {
  let raw: string | null
  try { raw = getStorage().getItem(`${DRAFT_PREFIX}${type}`) } catch { throw new DemoStorageError() }
  if (!raw) return null
  try {
    const draft: unknown = JSON.parse(raw)
    if (!isItemDraft(draft)) throw new Error('invalid draft')
    return draft
  } catch {
    throw new DemoStorageError('本地草稿已损坏，请清理浏览器站点数据后重试。')
  }
}

/** 保存当前类型的草稿快照；图片字段只保存 IndexedDB 编号。 */
export async function saveDraft(type: RecordType, draft: ItemDraft): Promise<void> {
  try { getStorage().setItem(`${DRAFT_PREFIX}${type}`, JSON.stringify(draft)) }
  catch { throw new DemoStorageError() }
}

/** 提交成功或用户确认重置后，删除对应类型的草稿。 */
export async function clearDraft(type: RecordType): Promise<void> {
  try { getStorage().removeItem(`${DRAFT_PREFIX}${type}`) }
  catch { throw new DemoStorageError() }
}

/** 成功条件是浏览器确实写入记录；失败时页面保留表单并可重试。 */
export async function publishLocalItem(type: RecordType, draft: ItemDraft): Promise<LocalItemRecord> {
  let records: LocalItemRecord[]
  try { records = parseArray(getStorage().getItem(RECORDS_KEY)) }
  catch (error) { if (error instanceof DemoStorageError) throw error; throw new DemoStorageError() }
  // demo 前缀明确区分浏览器演示编号与后端数据库的数字 ID。
  const record: LocalItemRecord = {
    id: `demo-${type}-${crypto.randomUUID()}`,
    type,
    title: draft.title.trim(),
    category: draft.category as ItemCategory,
    campus: draft.campus as LocalItemRecord['campus'],
    area: draft.campus === '东丽校区' ? draft.area as LocalItemRecord['area'] : '',
    location: draft.location.trim(),
    occurredAt: new Date(draft.occurredAt).toISOString(),
    description: draft.description.trim(),
    contactMasked: maskContact(draft.contact), // 演示记录只持久化脱敏后的联系方式。
    contactNote: draft.contactNote.trim(),
    ...(type === 'found' ? {
      storageMethod: draft.storageMethod as LocalItemRecord['storageMethod'],
      storageLocation: draft.storageLocation.trim(),
      contactWindow: draft.contactWindow.trim(),
    } : {}),
    imageIds: [...draft.imageIds],
    status: 'pending-match',
    createdAt: new Date().toISOString(),
  }
  if (!ITEM_CATEGORIES.includes(record.category)) throw new DemoStorageError('物品类别无效，请重新选择。')
  try { getStorage().setItem(RECORDS_KEY, JSON.stringify([record, ...records])) }
  catch { throw new DemoStorageError() }
  return record
}
