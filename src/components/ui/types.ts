/**
 * UI 组件共享的公开类型。
 * 单独放一个 .ts 而不是写在 `<script setup>` 里：script setup 不允许 export，
 * 靠类型擦除「碰巧能跑」的写法在换构建链时会炸。
 *
 * Toast 相关类型在 `@/composables/useToast` 里（那是唯一事实来源）。
 */

/** AppTabNav 的单个页签 */
export interface TabItem {
  key: string
  label: string
  /** 右侧数字角标，如调用统计条数 */
  count?: number
}

/** AppOperationCard 的单个操作项 */
export interface OperationItem {
  key: string
  label: string
  icon?: string
  description?: string
  tone?: 'default' | 'danger'
  disabled?: boolean
}

/** AppKeyValueList 的单行 */
export interface KeyValueItem {
  label: string
  value?: string | number | null
  variant?: 'text' | 'strong' | 'mono' | 'link'
  /** 整行占满（长文本） */
  block?: boolean
}
/** AppRowActions 的单个菜单项 */
export interface RowAction {
  key: string
  label: string
  icon?: string
  tone?: 'default' | 'danger'
}