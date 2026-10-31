<script setup lang="ts">
/**
 * 只读「标签 + 值」列表。6 个详情页（Agent / 知识库 / 数据集 / 工具 / 厂商 / 应用）的
 * 左信息卡与右统计卡都是这个结构，字段缺失必须兜底成「-」而不是渲染空白——
 * 原型里数据集详情页的「创建时间」就是空的。
 */
export interface KeyValueItem {
  label: string
  value?: string | number | null
  /** 值用主色/等宽等特殊样式 */
  variant?: 'text' | 'strong' | 'mono' | 'link'
  /** 整行占满（长文本） */
  block?: boolean
}

withDefaults(
  defineProps<{
    items: KeyValueItem[]
    /** 两列布局，宽屏详情页用 */
    columns?: 1 | 2
    /** 键值上下排列（默认）或左右排列 */
    orientation?: 'vertical' | 'horizontal'
    /** 缺失值兜底 */
    fallback?: string
  }>(),
  { columns: 1, orientation: 'vertical', fallback: '-' }
)

function display(value: KeyValueItem['value'], fallback: string): string {
  if (value === null || value === undefined || value === '') return fallback
  return String(value)
}
</script>

<template>
  <dl class="kv-list" :class="[`is-cols-${columns}`, `is-${orientation}`]">
    <div v-for="item in items" :key="item.label" class="kv-list__row" :class="{ 'is-block': item.block }">
      <dt class="kv-list__label">{{ item.label }}</dt>
      <dd class="kv-list__value" :class="item.variant ? `is-${item.variant}` : undefined">
        <slot :name="`value-${item.label}`" :item="item">{{ display(item.value, fallback) }}</slot>
      </dd>
    </div>
  </dl>
</template>

<style scoped>
.kv-list {
  display: grid;
  gap: var(--spacing-4);
  margin: 0;
}

.kv-list.is-cols-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: var(--spacing-6);
}

.kv-list__row {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  min-width: 0;
}

.kv-list__row.is-block {
  grid-column: 1 / -1;
}

.kv-list.is-horizontal .kv-list__row {
  flex-direction: row;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--spacing-4);
}

.kv-list__label {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  white-space: nowrap;
}

.kv-list__value {
  margin: 0;
  font: var(--font-body-md);
  color: var(--color-text-secondary);
  word-break: break-word;
}

.kv-list__value.is-strong {
  color: var(--color-text);
  font-weight: 500;
}

.kv-list__value.is-mono {
  font-family: var(--font-family-mono);
  font-size: 13px;
}

.kv-list__value.is-link {
  color: var(--color-primary);
  font-weight: 500;
  cursor: pointer;
}
</style>
