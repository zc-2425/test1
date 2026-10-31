/**
 * UI 基础组件统一出口。
 *
 * 命名统一加 `App` 前缀，避免与 Vuetify 的 V* 组件或 DOM 原生标签语义撞车。
 * 与 docs/03-组件与模式清单.md 的对应：
 *   PageHeader → AppPageHeader      ContentCard → AppContentCard
 *   AppDataTable                    StatusBadge → AppStatusBadge
 *   StatCard → AppStatCard          TagChip → AppTagChip
 *   ProgressInline → AppProgressInline   KeyValueList → AppKeyValueList
 *   EmptyState → AppEmptyState      AppModal / AppDrawer / AppToast / AppConfirmDialog
 *   FilterBar → AppFilterBar        TabNav → AppTabNav
 *   DetailHeader → AppDetailHeader  OperationCard → AppOperationCard
 */

// —— P3：骨架与数据展示 ——
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

// —— P4：表单与反馈 ——
export { default as AppButton } from './AppButton.vue'
export { default as AppTextField } from './AppTextField.vue'
export { default as AppSelect } from './AppSelect.vue'
export { default as AppTextarea } from './AppTextarea.vue'
export { default as AppSwitch } from './AppSwitch.vue'
export { default as AppSlider } from './AppSlider.vue'
export { default as AppTagInput } from './AppTagInput.vue'
export { default as AppFileUploader } from './AppFileUploader.vue'
export { default as AppModal } from './AppModal.vue'
export { default as AppDrawer } from './AppDrawer.vue'
export { default as AppToastHost } from './AppToastHost.vue'
export { default as AppConfirmHost } from './AppConfirmHost.vue'

// —— P4：页面级配方 ——
export { default as AppFilterBar } from './AppFilterBar.vue'
export { default as AppTabNav } from './AppTabNav.vue'
export { default as AppDetailHeader } from './AppDetailHeader.vue'
export { default as AppOperationCard } from './AppOperationCard.vue'
export { default as AppRowActions } from './AppRowActions.vue'

// —— 类型与常量 ——
export { STATUS_TONES, TYPE_CHIP_KEYS, toneOf } from './status-tones'
export type { KeyValueItem, OperationItem, RowAction, TabItem } from './types'
export type { TableColumn, SortState, PageResult, StatusTone, BadgeVariant } from '@/types/common'
export type { ToastTone, ToastOptions } from '@/composables/useToast'
