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

export function locationOptions(
  choices: CampusLocationOption[], campus: Campus | '', area: CampusArea | '' | null,
  anyArea = false,
): CampusLocationOption[] {
  if (!campus || (campus === '东丽校区' && !area && !anyArea)) return []
  return choices.filter((choice) => choice.campus === campus
    && (anyArea || choice.area === (area || null)))
}

export function isLocationSelection(
  choices: CampusLocationOption[], campus: Campus | '', area: CampusArea | '' | null,
  name: string, anyArea = false,
): boolean {
  return locationOptions(choices, campus, area, anyArea).some((choice) => choice.name === name)
}

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
