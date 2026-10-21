// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
// 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
/** 地点选项来自后端距离目录。 */
import { ref } from 'vue'
import { requestJson } from '../api/client'
import type { Campus, CampusArea } from '../types/item'

export interface CampusLocationOption {
  id: string
  name: string
  campus: Campus
  area: CampusArea | null
  simulated: boolean
}

// 文档对应：图2-2-2、图2-2-3 发生及保管地点的校区、区域筛选。
// 设计文档对应：图3-2-4、图3-2-7 按校区、区域筛选发生地点；保管地点可选择同校区任一区域。
export function locationOptions(
  choices: CampusLocationOption[], campus: Campus | '', area: CampusArea | '' | null,
  anyArea = false,
): CampusLocationOption[] {
  if (!campus || (campus === '东丽校区' && !area && !anyArea)) return []
  return choices.filter((choice) => choice.campus === campus
    && (anyArea || choice.area === (area || null)))
}

// 文档对应：图2-2-2、图2-2-3 的标准地点选择校验。
// 设计文档对应：图3-2-4、图3-2-7 校验选中值确实存在于服务端地点目录。
export function isLocationSelection(
  choices: CampusLocationOption[], campus: Campus | '', area: CampusArea | '' | null,
  name: string, anyArea = false,
): boolean {
  return locationOptions(choices, campus, area, anyArea).some((choice) => choice.name === name)
}

// 文档对应：图2-2-2、图2-2-3 的地点目录加载；2.2.10节公开地点接口。
// 设计文档对应：图3-2-4、图3-2-7、图4-2 共用地点加载状态；组件将 load 重命名为 loadLocations。
export function useCampusLocations() {
  const choices = ref<CampusLocationOption[]>([])
  const loading = ref(false)
  const error = ref('')
  async function load() {
    if (loading.value) return
    loading.value = true
    error.value = ''
    try {
      choices.value = await requestJson<CampusLocationOption[]>('/api/v1/locations')
    } catch {
      error.value = '地点选项加载失败，请重试。'
    } finally {
      loading.value = false
    }
  }
  return { choices, loading, error, load }
}
