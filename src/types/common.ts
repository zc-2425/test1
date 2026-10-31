/** 跨组件共享的基础类型 */

/** 后端统一分页信封，对应 FastAPI 的 Page[T] */
export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  size: number
}

/** 状态色调：只表达语义，具体颜色由 StatusBadge 决定 */
export type StatusTone =
  | 'success'
  | 'running'
  | 'warning'
  | 'danger'
  | 'neutral'
  | 'info'
  | 'accent'

/** 徽章形态：列表页用 solid（原型如此），详情页可用 text（原型里详情页退化为纯色文字） */
export type BadgeVariant = 'solid' | 'soft' | 'text'

/** 表格列定义：数据驱动，避免每个列表页写一遍 <table> */
export interface TableColumn {
  /** 字段名，同时用于取默认的 #cell-<key> 插槽 */
  key: string
  title: string
  width?: string
  align?: 'left' | 'center' | 'right'
  /** 默认渲染成什么，custom 表示完全交给插槽 */
  render?: 'text' | 'badge' | 'tag' | 'progress' | 'mono' | 'actions' | 'custom'
  /** 首列用主色加粗（原型里「工作流/应用/Agent 名称」是紫色可点） */
  emphasis?: boolean
  /** 开启后表头出现排序箭头，点击派发 sort 事件 */
  sortable?: boolean
  /** 省略号截断 */
  ellipsis?: boolean
}

export interface SortState {
  key: string
  order: 'asc' | 'desc'
}
