import { reactive, readonly } from 'vue'

/**
 * 轻量 Toast。
 *
 * 为什么不做成 Context/Provide：这类「全局单例 UI」用模块级 reactive 最省事，
 * 页面里 `toast('已保存')` 即可，不需要在组件树里层层 provide；
 * 渲染由 App.vue 挂载的 <AppToastHost /> 负责（Teleport 到 body）。
 *
 * 注意：模块级状态在 SSR 下会跨请求共享，本项目是纯 SPA，不存在这个问题。
 */

export type ToastTone = 'success' | 'error' | 'warning' | 'info'

export interface ToastOptions {
  title: string
  description?: string
  tone?: ToastTone
  /** 毫秒，0 表示不自动关闭 */
  duration?: number
}

export interface ToastItem extends ToastOptions {
  id: number
}

const items = reactive<ToastItem[]>([])
let seed = 0

/** 默认停留时长：错误给久一点，成功短一点 */
const DEFAULT_DURATION: Record<ToastTone, number> = {
  success: 2400,
  info: 2600,
  warning: 3200,
  error: 4200
}

export function dismissToast(id: number): void {
  const index = items.findIndex((item) => item.id === id)
  if (index >= 0) items.splice(index, 1)
}

export function pushToast(options: ToastOptions): number {
  seed += 1
  const tone = options.tone ?? 'success'
  const item: ToastItem = {
    ...options,
    id: seed,
    tone,
    duration: options.duration ?? DEFAULT_DURATION[tone]
  }
  items.push(item)
  if (item.duration && item.duration > 0) {
    window.setTimeout(() => dismissToast(item.id), item.duration)
  }
  return item.id
}

/** 简写：toast('已保存') / toast('删除失败', { tone: 'error' }) */
export function toast(
  title: string,
  options: Omit<ToastOptions, 'title'> = {}
): number {
  return pushToast({ title, ...options })
}

export function useToasts() {
  return { items: readonly(items), pushToast, dismissToast, toast }
}
