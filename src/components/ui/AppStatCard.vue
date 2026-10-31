<script setup lang="ts">
import type { StatusTone } from '@/types/common'

/**
 * 统计卡：探索页 4 卡（图标在上、数字居中）与 LLMOps 6 卡（图标在左）两种版式。
 * 数字支持格式化，避免页面里到处写 toLocaleString。
 */
const props = withDefaults(
  defineProps<{
    icon: string
    value: number | string
    label: string
    tone?: StatusTone
    layout?: 'top' | 'inline'
    /** 千分位 + 缩写（11.8K），默认对数字生效 */
    compactNumber?: boolean
    /** 环比等附注 */
    hint?: string
  }>(),
  { tone: 'accent', layout: 'top', compactNumber: true }
)

function formatValue(): string {
  const { value, compactNumber } = props
  if (typeof value !== 'number') return value
  if (!compactNumber) return value.toLocaleString('zh-CN')
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (value >= 10_000) return `${(value / 1000).toFixed(1)}K`
  return value.toLocaleString('zh-CN')
}
</script>

<template>
  <div class="stat-card" :class="`is-${layout}`">
    <span class="stat-card__icon" :class="`is-${tone}`">
      <i :class="['mdi', icon]" aria-hidden="true" />
    </span>
    <div class="stat-card__text">
      <span class="stat-card__value">{{ formatValue() }}</span>
      <span class="stat-card__label">{{ label }}</span>
      <span v-if="hint" class="stat-card__hint">{{ hint }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  display: flex;
  background: var(--color-surface);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-4);
  min-width: 0;
}

.stat-card.is-top {
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-2);
  text-align: center;
  padding: var(--spacing-5) var(--spacing-4);
}

.stat-card.is-inline {
  flex-direction: row;
  align-items: center;
  gap: var(--spacing-3);
}

.stat-card__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  font-size: 18px;
  flex: 0 0 auto;
}

.stat-card__icon.is-accent {
  color: var(--color-primary);
  background: var(--color-primary-container);
}
.stat-card__icon.is-success {
  color: var(--status-success);
  background: var(--status-success-bg);
}
.stat-card__icon.is-running {
  color: var(--status-running);
  background: rgba(27, 136, 202, 0.12);
}
.stat-card__icon.is-warning {
  color: var(--status-warning);
  background: var(--status-warning-bg);
}
.stat-card__icon.is-danger {
  color: var(--status-danger);
  background: var(--status-danger-bg);
}
.stat-card__icon.is-info {
  color: var(--status-info);
  background: rgba(25, 118, 210, 0.12);
}
.stat-card__icon.is-neutral {
  color: var(--color-text-secondary);
  background: var(--color-surface-container);
}

.stat-card__text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 2px;
}

.is-top .stat-card__text {
  align-items: center;
}

.stat-card__value {
  font: var(--font-stat);
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.stat-card__label {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.stat-card__hint {
  font: var(--font-label-sm);
  color: var(--status-success);
}
</style>
