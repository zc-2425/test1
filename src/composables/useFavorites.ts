import { computed, ref } from 'vue'

/**
 * 收藏状态（探索页的心形）。
 *
 * 后端没有 favorites 表，也不打算为这个练手项目加一个 —— 收藏是纯本地偏好，
 * 放 localStorage 反而更合适（换浏览器不同步，但这里就一台机器）。
 * 用模块级 ref，多个页面共享同一份，不会出现「两个页面各记一份」的错乱。
 */

const STORAGE_KEY = 'aiap:favorites'

function read(): string[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    const parsed: unknown = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === 'string') : []
  } catch {
    // localStorage 被禁用或内容损坏时退化成空列表，不要让页面挂掉
    return []
  }
}

const favorites = ref<string[]>(read())

function persist(): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites.value))
  } catch {
    /* 隐私模式下写入失败，忽略即可 */
  }
}

export function useFavorites() {
  function isFavorite(key: string): boolean {
    return favorites.value.includes(key)
  }

  function toggle(key: string): boolean {
    const index = favorites.value.indexOf(key)
    if (index >= 0) {
      favorites.value = favorites.value.filter((item) => item !== key)
      persist()
      return false
    }
    favorites.value = [...favorites.value, key]
    persist()
    return true
  }

  const count = computed(() => favorites.value.length)

  return { favorites, count, isFavorite, toggle }
}
