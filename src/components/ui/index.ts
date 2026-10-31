/**
 * UI 基础组件统一出口。
 * 命名统一加 `App` 前缀，避免与 Vuetify 的 V* 组件或 DOM 原生标签语义撞车。
 *
 * 与 docs/03-组件与模式清单.md 的命名对应：
 *   PageHeader      → AppPageHeader
 *   ContentCard     → AppContentCard
 *   AppDataTable    → AppDataTable
 *   StatusBadge     → AppStatusBadge
 *   StatCard        → AppStatCard
 *   TagChip         → AppTagChip
 *   ProgressInline  → AppProgressInline
 *   KeyValueList    → AppKeyValueList
 *   EmptyState      → AppEmptyState
 */
export { default as AppPageHeader } from './AppPageHeader.vue'
export { default as AppContentCard } from './AppContentCard.vue'
export { default as AppDataTable } from './AppDataTable.vue'
export { default as AppPagination } from './AppPagination.vue'
export { default as AppStatusBadge } from './AppStatusBadge.vue'
export { default as AppTagChip } from './AppTagChip.vue'
export { default as AppStatCard } from './AppStatCard.vue'
export { default as AppProgressInline } from './AppProgressInline.vue'
export { default as AppKeyValueList } from './AppKeyValueList.vue'
export { default as AppEmptyState } from './AppEmptyState.vue'

export { STATUS_TONES, TYPE_CHIP_KEYS, toneOf } from './status-tones'
export type { KeyValueItem } from './AppKeyValueList.vue'
export type { TableColumn, SortState, PageResult, StatusTone, BadgeVariant } from '@/types/common'
