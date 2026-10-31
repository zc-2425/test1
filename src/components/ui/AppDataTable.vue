<script setup lang="ts">
import { computed, ref, useSlots } from 'vue'
import type { SortState, TableColumn } from '@/types/common'
import AppEmptyState from './AppEmptyState.vue'
import AppProgressInline from './AppProgressInline.vue'
import AppStatusBadge from './AppStatusBadge.vue'
import AppTagChip from './AppTagChip.vue'

type Row = Record<string, unknown>

/**
 * 数据表格：列定义驱动，一个组件吃掉 7 个列表页。
 *
 * 为什么不用 Vuetify 的 VDataTable：
 * 1. 原型表头是灰底 `#FAFAFA` + 13px/500，行高 52px，行悬停是**橙色**——VDataTable 的默认
 *    悬停是 onSurface 黑色叠加，覆盖起来反而更绕；
 * 2. 列宽需要精确控制（colgroup），且首列是紫色可点名称；
 * 3. 排序/分页做成受控（emit 事件），后端分页时页面只传参数不搬数据。
 */
const props = withDefaults(
  defineProps<{
    columns: TableColumn[]
    rows: Row[]
    rowKey?: string
    loading?: boolean
    emptyTitle?: string
    emptyDescription?: string
    emptyIcon?: string
    /** 行可点（列表 → 详情） */
    clickableRows?: boolean
    /** 紧凑行高，用于详情页内嵌小表 */
    dense?: boolean
    /** 开启纵向滚动 + 表头吸顶，如 '520px' */
    maxHeight?: string
    /** 空数据显示（配合筛选） */
    filtered?: boolean
  }>(),
  {
    rowKey: 'id',
    loading: false,
    emptyTitle: '暂无数据',
    emptyDescription: '',
    emptyIcon: 'mdi-inbox-outline',
    clickableRows: false,
    dense: false,
    filtered: false
  }
)

const emit = defineEmits<{
  (e: 'row-click', row: Row, index: number): void
  (e: 'sort', state: SortState): void
}>()

const slots = useSlots()
const sortState = ref<SortState | null>(null)

function onHeaderClick(col: TableColumn): void {
  if (!col.sortable) return
  const next: SortState =
    sortState.value?.key === col.key
      ? { key: col.key, order: sortState.value.order === 'asc' ? 'desc' : 'asc' }
      : { key: col.key, order: 'asc' }
  sortState.value = next
  emit('sort', next)
}

function sortIcon(col: TableColumn): string {
  if (!col.sortable) return ''
  if (sortState.value?.key !== col.key) return 'mdi-unfold-more-horizontal'
  return sortState.value.order === 'asc' ? 'mdi-chevron-up' : 'mdi-chevron-down'
}

function display(value: unknown): string {
  if (value === null || value === undefined || value === '') return '-'
  return String(value)
}

function rowId(row: Row, index: number): string {
  const id = row[props.rowKey]
  return id === null || id === undefined ? `row-${index}` : String(id)
}

const hasActionsSlot = computed(() => !!slots.actions)
const skeletonRows = computed(() => Array.from({ length: 5 }, (_, i) => i))
</script>

<template>
  <div class="data-table" :class="{ 'is-dense': dense }">
    <div v-if="$slots.toolbar" class="data-table__toolbar">
      <slot name="toolbar" />
    </div>

    <div class="data-table__scroll" :style="maxHeight ? { maxHeight } : undefined">
      <table>
        <colgroup>
          <col v-for="col in columns" :key="col.key" :style="col.width ? { width: col.width } : undefined" />
        </colgroup>

        <thead>
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              :class="[col.align ? `is-${col.align}` : '', { 'is-sortable': col.sortable }]"
              @click="onHeaderClick(col)"
            >
              <span class="th-inner">
                {{ col.title }}
                <i
                  v-if="col.sortable"
                  :class="[
                    'mdi',
                    sortIcon(col),
                    'th-sort',
                    { 'is-active': sortState?.key === col.key }
                  ]"
                  aria-hidden="true"
                />
              </span>
            </th>
          </tr>
        </thead>

        <!-- 加载骨架 -->
        <tbody v-if="loading">
          <tr v-for="i in skeletonRows" :key="i" class="is-skeleton">
            <td v-for="col in columns" :key="col.key">
              <span class="skeleton-bar" :style="{ width: `${50 + ((i * 13) % 40)}%` }" />
            </td>
          </tr>
        </tbody>

        <!-- 数据行 -->
        <tbody v-else-if="rows.length">
          <tr
            v-for="(row, index) in rows"
            :key="rowId(row, index)"
            :class="{ 'is-clickable': clickableRows }"
            @click="clickableRows && emit('row-click', row, index)"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              :class="[col.align ? `is-${col.align}` : '', { 'is-actions': col.render === 'actions' }]"
            >
              <!-- 页面自定义单元格优先 -->
              <slot
                v-if="slots[`cell-${col.key}`]"
                :name="`cell-${col.key}`"
                :row="row"
                :value="row[col.key]"
                :index="index"
              />
              <slot
                v-else-if="col.render === 'actions' && hasActionsSlot"
                name="actions"
                :row="row"
                :index="index"
              />
              <AppStatusBadge v-else-if="col.render === 'badge'" :status="display(row[col.key])" />
              <AppTagChip v-else-if="col.render === 'tag'" :label="display(row[col.key])" />
              <AppProgressInline
                v-else-if="col.render === 'progress'"
                :value="Number(row[col.key] ?? 0)"
              />
              <span v-else-if="col.render === 'mono'" class="cell-mono">{{
                display(row[col.key])
              }}</span>
              <span
                v-else
                :class="{ 'cell-emphasis': col.emphasis, 'cell-ellipsis': col.ellipsis }"
                >{{ display(row[col.key]) }}</span
              >
            </td>
          </tr>
        </tbody>

        <!-- 空态 -->
        <tbody v-else>
          <tr class="is-empty">
            <td :colspan="columns.length">
              <AppEmptyState
                :icon="filtered ? 'mdi-magnify-close' : emptyIcon"
                :title="filtered ? '没有匹配的结果' : emptyTitle"
                :description="filtered ? '试试换个关键字，或清空筛选条件' : emptyDescription"
                size="sm"
              >
                <template v-if="$slots['empty-action']" #action>
                  <slot name="empty-action" />
                </template>
              </AppEmptyState>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="$slots.footer" class="data-table__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<style scoped>
.data-table {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.data-table__toolbar {
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: var(--border-width) solid var(--color-divider);
}

.data-table__scroll {
  overflow: auto;
  min-width: 0;
}

table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
}

thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  height: var(--table-header-height);
  padding: 0 var(--spacing-4);
  background: var(--color-surface-header);
  font: var(--font-label-md);
  color: var(--color-text);
  text-align: left;
  font-weight: 500;
  white-space: nowrap;
  border-bottom: var(--border-width) solid var(--color-divider);
}

thead th.is-sortable {
  cursor: pointer;
  user-select: none;
}

thead th.is-sortable:hover {
  color: var(--color-primary);
}

.th-inner {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.th-sort {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.th-sort.is-active {
  color: var(--color-primary);
}

tbody td {
  height: var(--table-row-height);
  padding: 0 var(--spacing-4);
  font: var(--font-body-md);
  color: var(--color-text-secondary);
  border-bottom: var(--border-width) solid var(--color-divider);
  vertical-align: middle;
}

.data-table.is-dense tbody td {
  height: 40px;
}

tbody tr:last-child td {
  border-bottom: 0;
}

/* 行悬停是橙色 —— 原型里工具列表整行悬停就是橙色，这是它最有辨识度的交互 */
tbody tr:not(.is-empty):not(.is-skeleton):hover td {
  background: var(--color-accent-soft);
}

tbody tr.is-clickable {
  cursor: pointer;
}

.cell-emphasis {
  color: var(--color-primary);
  font-weight: 500;
}

.cell-ellipsis {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-mono {
  font-family: var(--font-family-mono);
  font-size: 13px;
  color: var(--color-text-secondary);
}

td.is-center,
th.is-center {
  text-align: center;
}

td.is-right,
th.is-right {
  text-align: right;
}

td.is-actions {
  white-space: nowrap;
}

.is-empty td {
  height: auto;
  border-bottom: 0;
}

.is-skeleton td {
  background: transparent;
}

.skeleton-bar {
  display: block;
  height: 10px;
  border-radius: var(--radius-full);
  background: linear-gradient(
    90deg,
    var(--color-surface-container) 25%,
    var(--color-surface-variant) 37%,
    var(--color-surface-container) 63%
  );
  background-size: 400% 100%;
  animation: skeleton-shimmer 1.4s ease infinite;
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

.data-table__footer {
  border-top: var(--border-width) solid var(--color-divider);
  padding: var(--spacing-3) var(--spacing-4);
}
</style>
