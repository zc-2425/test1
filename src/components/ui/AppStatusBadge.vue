<script setup lang="ts">
import { computed } from 'vue'
import type { BadgeVariant, StatusTone } from '@/types/common'
import { toneOf } from './status-tones'

/**
 * 状态胶囊：状态词 → 颜色 的唯一出口。
 * 列表页用 solid（原型如此），详情页可传 variant="text" 还原原型里退化的纯色文字。
 */
const props = withDefaults(
  defineProps<{
    status: string | null | undefined
    /** 手工指定色调，覆盖字典（同一个词在不同实体含义不同时用） */
    tone?: StatusTone
    variant?: BadgeVariant
    /** 未知状态显示兜底文案，禁止渲染空白 */
    fallback?: string
  }>(),
  { variant: 'solid', fallback: '未知' }
)

const text = computed(() => props.status?.trim() || props.fallback)
const resolvedTone = computed<StatusTone>(() => props.tone ?? toneOf(text.value))
</script>

<template>
  <span class="status-badge" :class="[`is-${resolvedTone}`, `is-${variant}`]">{{ text }}</span>
</template>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 22px;
  padding: 0 10px;
  border-radius: var(--radius-full);
  font-size: 12px;
  line-height: 1;
  font-weight: 500;
  white-space: nowrap;
  border: 1px solid transparent;
}

/* —— solid：白字实底，列表页用 —— */
.is-solid.is-success {
  background: var(--status-success);
  color: #fff;
}
.is-solid.is-running {
  background: var(--status-running);
  color: #fff;
}
.is-solid.is-warning {
  background: var(--status-warning);
  color: #fff;
}
.is-solid.is-danger {
  background: var(--status-danger);
  color: #fff;
}
.is-solid.is-neutral {
  background: var(--status-neutral);
  color: #fff;
}
.is-solid.is-info {
  background: var(--status-info);
  color: #fff;
}
.is-solid.is-accent {
  background: var(--status-accent);
  color: #fff;
}

/* —— soft：浅底深字，用于次要标记 —— */
.is-soft.is-success {
  background: var(--status-success-bg);
  color: var(--status-success);
}
.is-soft.is-running {
  background: rgba(27, 136, 202, 0.12);
  color: var(--status-running);
}
.is-soft.is-warning {
  background: var(--status-warning-bg);
  color: #9a4d00;
}
.is-soft.is-danger {
  background: var(--status-danger-bg);
  color: var(--status-danger);
}
.is-soft.is-neutral {
  background: var(--color-surface-container);
  color: var(--color-text-secondary);
}
.is-soft.is-info {
  background: rgba(25, 118, 210, 0.12);
  color: var(--status-info);
}
.is-soft.is-accent {
  background: var(--color-primary-container);
  color: var(--color-primary);
}

/* —— text：无底色，纯文字（详情页状态） —— */
.is-text {
  padding: 0;
  height: auto;
  background: transparent;
  font-weight: 500;
}
.is-text.is-success {
  color: var(--status-success);
}
.is-text.is-running {
  color: var(--status-running);
}
.is-text.is-warning {
  color: var(--status-warning);
}
.is-text.is-danger {
  color: var(--status-danger);
}
.is-text.is-neutral {
  color: var(--color-text-tertiary);
}
.is-text.is-info {
  color: var(--status-info);
}
.is-text.is-accent {
  color: var(--color-primary);
}
</style>
