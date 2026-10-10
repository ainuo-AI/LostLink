import { toLostFoundItem } from '../api/items'
import type { ApiItem, ItemStatus } from '../types/item'

const lostStatuses: ItemStatus[] = ['active', 'active', 'active', 'active', 'recovered', 'closed', 'active', 'closed']
const foundStatuses: ItemStatus[] = ['active', 'active', 'active', 'active', 'returned', 'closed', 'active', 'closed']

// 不提供演示身份、角色或写操作；这些物品只供开发预览，不对应真实账户。
export const profileDemoItems = Array.from({ length: 16 }, (_, index) => {
  const isLost = index < 8
  const item: ApiItem = {
    id: index + 1,
    type: isLost ? 'lost' : 'found',
    category: isLost ? '箱包' : '数码',
    title: `【开发演示】${isLost ? '蓝色背包' : '白色耳机'} ${index % 8 + 1}`,
    description: '虚构物品，仅用于检查个人页布局、筛选、分页和详情。',
    location: '演示地点',
    campus: '东丽校区',
    area: '北区',
    occurred_at: '2026-09-30T08:30:00Z',
    status: (isLost ? lostStatuses : foundStatuses)[index % 8],
    contact_hint: '开发演示，无真实联系人。',
    contact: null,
    contact_note: null,
  }
  return toLostFoundItem(item)
})
