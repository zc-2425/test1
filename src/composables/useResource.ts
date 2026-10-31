import { onMounted, ref, type Ref } from 'vue'

/**
 * 单资源加载：`/api/agents/:id` 这类「进页面拿一条数据」的通用状态机。
 * 详情页 7 个都是这个形状，抽象掉之后每页只剩渲染。
 *
 * 与 useListQuery 的区别：那个管分页列表，这个管单条 + 404。
 */
export interface UseResourceOptions {
  /** 是否在 onMounted 自动拉取，默认 true */
  immediate?: boolean
}

export function useResource<T>(fetcher: () => Promise<T>, options: UseResourceOptions = {}) {
  const { immediate = true } = options

  const data = ref(null) as Ref<T | null>
  const loading = ref(false)
  const error = ref<string | null>(null)
  /** 资源不存在（后端 404）单独标记，页面用它渲染空态而不是报错条 */
  const notFound = ref(false)

  async function reload(): Promise<void> {
    loading.value = true
    error.value = null
    notFound.value = false
    try {
      data.value = await fetcher()
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : String(cause)
      error.value = message
      data.value = null
      // ApiError 的 status 在 message 里体现为「不存在」，这里用关键字兜底判断
      notFound.value = message.includes('不存在') || message.includes('404')
    } finally {
      loading.value = false
    }
  }

  if (immediate) onMounted(() => void reload())

  return { data, loading, error, notFound, reload }
}
