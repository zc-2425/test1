import { computed, onMounted, ref, watch, type Ref } from 'vue'
import type { PageResult, SortState } from '@/types/common'
import type { ListQuery } from '@/api/types'

/**
 * 列表页的查询状态机：分页 + 关键字防抖 + 状态下拉 + 类型下拉 + 排序。
 *
 * 7 个列表页的这部分逻辑一字不差，抽出来之后每页只剩「列定义 + 行内操作」。
 * 刻意不用 Pinia：列表状态是本页私有，进 store 只会多一层间接，
 * 等真出现跨页共享（如全局筛选记忆）再上。
 */
export interface UseListQueryOptions {
  defaultSize?: number
  defaultSort?: SortState
  /** 关键字防抖毫秒 */
  debounce?: number
}

export function useListQuery<T>(
  fetcher: (query: ListQuery) => Promise<PageResult<T>>,
  options: UseListQueryOptions = {}
) {
  const { defaultSize = 10, defaultSort, debounce = 300 } = options

  const rows = ref([]) as Ref<T[]>
  const total = ref(0)
  const page = ref(1)
  const size = ref(defaultSize)
  const keyword = ref('')
  const status = ref<string | null>(null)
  const type = ref<string | null>(null)
  const sort = ref<SortState | null>(defaultSort ?? { key: 'created_at', order: 'desc' })
  const loading = ref(false)
  const error = ref<string | null>(null)

  let timer: number | undefined

  async function reload(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const result = await fetcher({
        page: page.value,
        size: size.value,
        q: keyword.value.trim() || undefined,
        status: status.value || undefined,
        type: type.value || undefined,
        sort: sort.value?.key,
        order: sort.value?.order
      })
      rows.value = result.items
      total.value = result.total
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      rows.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  /** 表头点击：同列再点切方向 */
  function onSort(state: SortState): void {
    sort.value = state
    page.value = 1
  }

  function resetFilters(): void {
    keyword.value = ''
    status.value = null
    type.value = null
    page.value = 1
  }

  function changePage(value: number): void {
    page.value = value
  }

  function changeSize(value: number): void {
    size.value = value
    page.value = 1
  }

  // 分页/筛选/排序变化立即重新请求（不防抖，这些是明确动作）
  watch([page, size, sort, status, type], () => void reload())

  // 关键字防抖，避免每敲一个字打一次接口
  watch(keyword, () => {
    window.clearTimeout(timer)
    timer = window.setTimeout(() => {
      page.value = 1
      void reload()
    }, debounce)
  })

  onMounted(() => void reload())

  const filtered = computed(
    () => Boolean(keyword.value.trim()) || Boolean(status.value) || Boolean(type.value)
  )

  return {
    rows,
    total,
    page,
    size,
    keyword,
    status,
    type,
    sort,
    loading,
    error,
    reload,
    onSort,
    resetFilters,
    filtered,
    changePage,
    changeSize
  }
}
