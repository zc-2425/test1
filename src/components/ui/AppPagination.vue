<script setup lang="ts">
import { computed } from 'vue'

/**
 * 分页器。原型 62 页里一个都没有（这是它最明显的产品缺陷），但 7 个列表页都需要，
 * 所以补齐并做成受控组件：只 emit 事件，数据由页面按新参数重新请求。
 */
const props = withDefaults(
  defineProps<{
    page: number
    size: number
    total: number
    sizeOptions?: number[]
    disabled?: boolean
  }>(),
  { sizeOptions: () => [10, 20, 50], disabled: false }
)

const emit = defineEmits<{
  (e: 'update:page', value: number): void
  (e: 'update:size', value: number): void
}>()

const pageCount = computed(() => Math.max(1, Math.ceil(props.total / props.size)))

/** 页数多时折叠：1 … 4 5 6 … 20 */
const pageItems = computed<(number | 'gap')[]>(() => {
  const count = pageCount.value
  const current = props.page
  if (count <= 7) return Array.from({ length: count }, (_, i) => i + 1)

  const items: (number | 'gap')[] = [1]
  const start = Math.max(2, current - 1)
  const end = Math.min(count - 1, current + 1)
  if (start > 2) items.push('gap')
  for (let i = start; i <= end; i += 1) items.push(i)
  if (end < count - 1) items.push('gap')
  items.push(count)
  return items
})

const rangeText = computed(() => {
  if (props.total === 0) return '共 0 条'
  const from = (props.page - 1) * props.size + 1
  const to = Math.min(props.page * props.size, props.total)
  return `第 ${from}–${to} 条，共 ${props.total} 条`
})

function go(target: number): void {
  if (props.disabled) return
  const next = Math.min(Math.max(1, target), pageCount.value)
  if (next !== props.page) emit('update:page', next)
}

function changeSize(event: Event): void {
  const value = Number((event.target as HTMLSelectElement).value)
  emit('update:size', value)
  emit('update:page', 1)
}
</script>

<template>
  <div class="pagination">
    <span class="pagination__info">{{ rangeText }}</span>

    <div class="pagination__controls">
      <select
        class="pagination__size"
        :value="size"
        :disabled="disabled"
        aria-label="每页条数"
        @change="changeSize"
      >
        <option v-for="opt in sizeOptions" :key="opt" :value="opt">{{ opt }} 条/页</option>
      </select>

      <button
        type="button"
        class="pagination__btn"
        :disabled="disabled || page <= 1"
        aria-label="上一页"
        @click="go(page - 1)"
      >
        <i class="mdi mdi-chevron-left" aria-hidden="true" />
      </button>

      <template v-for="(item, index) in pageItems" :key="`${item}-${index}`">
        <span v-if="item === 'gap'" class="pagination__gap">…</span>
        <button
          v-else
          type="button"
          class="pagination__btn"
          :class="{ 'is-current': item === page }"
          :disabled="disabled"
          @click="go(item)"
        >
          {{ item }}
        </button>
      </template>

      <button
        type="button"
        class="pagination__btn"
        :disabled="disabled || page >= pageCount"
        aria-label="下一页"
        @click="go(page + 1)"
      >
        <i class="mdi mdi-chevron-right" aria-hidden="true" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-4);
  flex-wrap: wrap;
}

.pagination__info {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.pagination__controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.pagination__size {
  height: 30px;
  margin-right: var(--spacing-2);
  padding: 0 var(--spacing-2);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 12px;
  cursor: pointer;
}

.pagination__btn {
  min-width: 30px;
  height: 30px;
  padding: 0 var(--spacing-2);
  border: var(--border-width) solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 13px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition:
    background-color var(--motion-fast) var(--motion-ease),
    border-color var(--motion-fast) var(--motion-ease);
}

.pagination__btn:hover:not(:disabled) {
  background: var(--color-surface-container);
}

.pagination__btn.is-current {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font-weight: 500;
}

.pagination__btn:disabled {
  color: var(--color-text-disabled);
  cursor: not-allowed;
}

.pagination__gap {
  padding: 0 var(--spacing-1);
  color: var(--color-text-tertiary);
  font-size: 13px;
}
</style>
