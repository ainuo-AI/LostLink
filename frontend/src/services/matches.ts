/**
 * 匹配通知与反馈的前端模拟服务
 *
 * 负责初始化演示通知、按时间读取、标记已读以及保存确认/拒绝结果。
 * 所有得分和解释都是固定演示数据，不调用 AI，也不能解释为找回概率。
 */
import type { MatchDimension, MatchItem, MatchNotification, MatchStatus } from '../types/demo'
import { DemoStorageError } from './localItems'

const MATCHES_KEY = 'lostlink:demo:matches:v1'

/** 类型守卫负责检查 localStorage 解析出的未知数据，防止损坏结构进入页面。 */
function isObject(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function isMatchItem(value: unknown): value is MatchItem {
  return isObject(value) && ['title', 'category', 'description', 'campus', 'location', 'occurredAt', 'icon'].every((key) => typeof value[key] === 'string')
}

function isMatchNotification(value: unknown): value is MatchNotification {
  return isObject(value)
    && ['id', 'title', 'summary', 'createdAt'].every((key) => typeof value[key] === 'string')
    && !Number.isNaN(Date.parse(value.createdAt as string))
    && typeof value.read === 'boolean'
    && ['pending', 'confirmed', 'rejected'].includes(String(value.status))
    && isMatchItem(value.mine) && isMatchItem(value.candidate)
    && typeof value.score === 'number' && Number.isFinite(value.score)
    && Array.isArray(value.dimensions)
    && value.dimensions.every((dimension: unknown) => isObject(dimension) && typeof dimension.label === 'string' && typeof dimension.explanation === 'string' && (dimension.score === null || (typeof dimension.score === 'number' && Number.isFinite(dimension.score))))
}

/** 生成五个展示维度；当前没有真实图片，所以图片维度明确标记为未评估。 */
function dimensions(seed: number): MatchDimension[] {
  return [
    { label: '图片', score: null, explanation: '双方均未提供实物照片，图片维度未评估；综合分为独立演示数据。' },
    { label: '文本', score: seed + 2, explanation: '模拟比较名称、描述和独有标记。' },
    { label: '属性', score: seed + 4, explanation: '模拟比较类别、颜色等结构化属性。' },
    { label: '地点', score: seed - 3, explanation: '模拟估计两个地点在校园内的接近程度。' },
    { label: '时间', score: seed - 1, explanation: '模拟比较丢失与拾获时间的先后和间隔。' },
  ]
}

/** 构造一条用于左右对比的演示物品，减少初始化数据中的重复字段。 */
function matchItem(title: string, category: string, description: string, location: string, icon: string): MatchItem {
  return { title, category, description, campus: '东丽校区', location, occurredAt: new Date(Date.now() - 86_400_000).toISOString(), icon }
}

/**
 * 首次访问时写入的校园演示数据，覆盖未读、已读、待处理、已确认、
 * 已拒绝和无图场景。之后刷新页面不会再次覆盖用户操作。
 */
function initialMatches(): MatchNotification[] {
  const hoursAgo = (hours: number) => new Date(Date.now() - hours * 3_600_000).toISOString()
  const bag = matchItem('黑色双肩包', '箱包', '白色小熊徽章，包内有教材。', '图书馆二层', '🎒')
  const bagFound = matchItem('拾到黑色背包', '箱包', '包上有白色徽章，暂存在教学楼值班室。', '教学楼 A 座', '🎒')
  const card = matchItem('蓝色校园卡套', '卡证', '蓝色挂绳与透明卡套。', '教学楼 A 座', '🪪')
  const earbuds = matchItem('白色无线耳机', '数码', '白色充电仓，外壳有轻微划痕。', '操场南门', '🎧')
  const book = matchItem('软件工程导论', '书籍', '封面深蓝色，扉页有姓名。', '实验楼 4 楼', '📘')
  return [
    { id: 'demo-match-1', title: '发现一条背包候选线索', summary: '外观标记与地点较接近，请查看后再决定。', createdAt: hoursAgo(1), read: false, status: 'pending', mine: bag, candidate: bagFound, score: 88, dimensions: dimensions(88) },
    { id: 'demo-match-2', title: '校园卡套有新的候选记录', summary: '卡套颜色与挂绳描述相近。', createdAt: hoursAgo(4), read: false, status: 'pending', mine: card, candidate: matchItem('拾到蓝色卡套', '卡证', '透明卡套，蓝色挂绳。', '教学楼 B 座', '🪪'), score: 83, dimensions: dimensions(83) },
    { id: 'demo-match-3', title: '耳机候选已确认', summary: '你已接受这条候选，还需要后续身份核验。', createdAt: hoursAgo(18), read: true, status: 'confirmed', mine: earbuds, candidate: matchItem('白色耳机充电仓', '数码', '白色外壳，有浅划痕。', '操场附近', '🎧'), score: 79, dimensions: dimensions(79) },
    { id: 'demo-match-4', title: '书籍候选已拒绝', summary: '你此前判断该候选与自己的物品不符。', createdAt: hoursAgo(28), read: true, status: 'rejected', mine: book, candidate: matchItem('一本课程教材', '书籍', '浅蓝封面，无姓名标记。', '图书馆一层', '📚'), score: 68, dimensions: dimensions(68), rejectionReason: '特征不符' },
    { id: 'demo-match-5', title: '一条无图的线索待查看', summary: '该候选未提供照片，可根据文字和地点判断。', createdAt: hoursAgo(39), read: false, status: 'pending', mine: book, candidate: matchItem('拾到一本教材', '书籍', '封面深蓝，具体版本待核验。', '实验楼', '📄'), score: 72, dimensions: dimensions(72) },
    { id: 'demo-match-6', title: '背包的另一条候选', summary: '时间与类别相近，但外观描述需进一步核对。', createdAt: hoursAgo(50), read: true, status: 'pending', mine: bag, candidate: matchItem('灰黑色书包', '箱包', '深色书包，拉链上有挂件。', '第二食堂', '🎒'), score: 64, dimensions: dimensions(64) },
  ]
}

function storage(): Storage {
  try { return window.localStorage } catch { throw new DemoStorageError() }
}

/** 读取并校验本地通知；数据损坏时提示用户处理，不静默重置状态。 */
function readMatches(): MatchNotification[] {
  let raw: string | null
  try { raw = storage().getItem(MATCHES_KEY) } catch { throw new DemoStorageError() }
  if (!raw) {
    const initial = initialMatches()
    writeMatches(initial)
    return initial
  }
  try {
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed) || !parsed.every(isMatchNotification)) throw new Error('invalid matches')
    return parsed
  } catch {
    throw new DemoStorageError('本地通知数据已损坏，可重新初始化演示数据。')
  }
}

/** 将通知数组作为一个快照写回，保证列表和详情读取同一份状态。 */
function writeMatches(matches: MatchNotification[]): void {
  try { storage().setItem(MATCHES_KEY, JSON.stringify(matches)) }
  catch { throw new DemoStorageError() }
}

/** 通知列表默认按时间倒序，最新通知排在最前。 */
export async function listMatchNotifications(): Promise<MatchNotification[]> {
  return readMatches().sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt))
}

/** 读取单条详情；找不到时返回 null，让页面显示资源不存在状态。 */
export async function getMatchNotification(id: string): Promise<MatchNotification | null> {
  return readMatches().find((item) => item.id === id) ?? null
}

/** 只更新 read，不改变 pending/confirmed/rejected 处理状态。 */
export async function markMatchRead(id: string): Promise<MatchNotification> {
  const matches = readMatches()
  const target = matches.find((item) => item.id === id)
  if (!target) throw new DemoStorageError('找不到这条匹配通知。')
  if (!target.read) {
    target.read = true
    writeMatches(matches)
  }
  return target
}

/** 批量清除未读数量，同样不会改变任何匹配处理结果。 */
export async function markAllMatchesRead(): Promise<void> {
  const matches = readMatches()
  if (!matches.some((item) => !item.read)) return
  matches.forEach((item) => { item.read = true })
  writeMatches(matches)
}

/**
 * 保存确认或拒绝决定。已处理记录直接报错，避免重复操作；
 * 原始综合分与维度解释保持不变，体现“反馈状态与模拟结果分离”。
 */
export async function decideMatch(id: string, decision: Exclude<MatchStatus, 'pending'>, reason = '', note = ''): Promise<MatchNotification> {
  const matches = readMatches()
  const target = matches.find((item) => item.id === id)
  if (!target) throw new DemoStorageError('找不到这条匹配通知。')
  if (target.status !== 'pending') throw new DemoStorageError('这条候选已处理，不能重复操作。')
  target.status = decision
  target.read = true
  if (decision === 'rejected') {
    target.rejectionReason = reason
    target.rejectionNote = note
  }
  // 仅修改处理与已读字段，原始模拟得分和解释保持不变。
  writeMatches(matches)
  return target
}

/** 只在用户明确点击“重置演示通知”时覆盖损坏或旧数据。 */
export async function resetMatchDemo(): Promise<MatchNotification[]> {
  const initial = initialMatches()
  writeMatches(initial)
  return initial
}
