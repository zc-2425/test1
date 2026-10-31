import { reactive } from 'vue'

/**
 * Promise 化的二次确认。
 *
 * 用法：
 *   const ok = await confirm({ title: '删除 Agent', description: '删除后不可恢复', tone: 'danger' })
 *   if (!ok) return
 *
 * 这样页面里不必为每个删除按钮各开一个 boolean 状态 + 一份弹窗模板，
 * 也不会出现「同时打开两个确认框」的竞态。
 */

export interface ConfirmOptions {
  title: string
  description?: string
  confirmText?: string
  cancelText?: string
  tone?: 'primary' | 'danger'
}

export interface ConfirmState extends ConfirmOptions {
  open: boolean
}

const state = reactive<ConfirmState>({
  open: false,
  title: '',
  confirmText: '确定',
  cancelText: '取消',
  tone: 'primary'
})

let resolver: ((value: boolean) => void) | null = null

export function confirm(options: ConfirmOptions): Promise<boolean> {
  // 若上一个还没结算，先按取消处理，避免 Promise 永远悬挂
  resolver?.(false)
  Object.assign(state, {
    confirmText: '确定',
    cancelText: '取消',
    tone: 'primary',
    description: undefined,
    ...options,
    open: true
  })
  return new Promise<boolean>((resolve) => {
    resolver = resolve
  })
}

export function useConfirmState(): ConfirmState {
  return state
}

export function settleConfirm(value: boolean): void {
  state.open = false
  resolver?.(value)
  resolver = null
}
