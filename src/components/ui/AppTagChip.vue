<script setup lang="ts">
import type { StatusTone } from '@/types/common'

/** 胶囊标签：分类、类型、功能点。与状态胶囊刻意区分（这里是浅灰/浅紫，不带绿色语义）。 */
withDefaults(
  defineProps<{
    label: string
    tone?: StatusTone
    /** 可点（分类筛选） */
    clickable?: boolean
    active?: boolean
  }>(),
  { tone: 'neutral', clickable: false, active: false }
)

defineEmits<{ (e: 'click'): void }>()
</script>

<template>
  <component
    :is="clickable ? 'button' : 'span'"
    :type="clickable ? 'button' : undefined"
    class="tag-chip"
    :class="[`is-${tone}`, { 'is-clickable': clickable, 'is-active': active }]"
    @click="clickable && $emit('click')"
  >
    <slot>{{ label }}</slot>
  </component>
</template>

<style scoped>
.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 22px;
  padding: 0 8px;
  border-radius: var(--radius-full);
  font-size: 12px;
  line-height: 1;
  font-weight: 400;
  white-space: nowrap;
  border: 1px solid transparent;
  background: var(--color-surface-container);
  color: var(--color-text-secondary);
  transition:
    background-color var(--motion-fast) var(--motion-ease),
    border-color var(--motion-fast) var(--motion-ease),
    color var(--motion-fast) var(--motion-ease);
}

.tag-chip.is-clickable {
  cursor: pointer;
  height: 32px;
  padding: 0 14px;
  font-size: 13px;
}

.tag-chip.is-clickable:hover {
  border-color: var(--color-border);
}

/* 分类 chips 的选中态用主色实底（探索页原型的「全部」是紫底白字） */
.tag-chip.is-active {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.tag-chip.is-accent {
  background: var(--color-primary-container);
  color: var(--color-primary);
}

.tag-chip.is-success {
  background: var(--status-success-bg);
  color: var(--status-success);
}

.tag-chip.is-warning {
  background: var(--status-warning-bg);
  color: #9a4d00;
}

.tag-chip.is-danger {
  background: var(--status-danger-bg);
  color: var(--status-danger);
}

.tag-chip.is-running {
  background: rgba(27, 136, 202, 0.12);
  color: var(--status-running);
}
</style>
