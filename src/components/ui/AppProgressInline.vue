<script setup lang="ts">
import { computed } from 'vue'

/**
 * 表格内细进度条 + 百分比。
 * 颜色随进度自动分档：<40 危险、<100 进行中、100 成功；
 * 也允许传 tone 覆盖（比如「失败」状态希望整条变红）。
 */
const props = withDefaults(
  defineProps<{
    value: number
    /** 进度条宽度，表格里通常给固定值 */
    width?: number
    showLabel?: boolean
    tone?: 'auto' | 'success' | 'running' | 'danger' | 'warning'
    /** 无进度数据时显示文案 */
    fallback?: string
  }>(),
  { width: 96, showLabel: true, tone: 'auto', fallback: '—' }
)

const clamped = computed(() => Math.max(0, Math.min(100, Math.round(props.value ?? 0))))

const resolvedTone = computed(() => {
  if (props.tone !== 'auto') return props.tone
  if (clamped.value >= 100) return 'success'
  if (clamped.value >= 40) return 'running'
  return 'warning'
})
</script>

<template>
  <div class="progress-inline">
    <div class="progress-inline__track" :style="{ width: `${width}px` }">
      <div
        class="progress-inline__bar"
        :class="`is-${resolvedTone}`"
        :style="{ width: `${clamped}%` }"
      />
    </div>
    <span v-if="showLabel" class="progress-inline__label">{{ clamped }}%</span>
  </div>
</template>

<style scoped>
.progress-inline {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
}

.progress-inline__track {
  height: 4px;
  border-radius: var(--radius-full);
  background: var(--color-surface-variant);
  overflow: hidden;
  flex: 0 0 auto;
}

.progress-inline__bar {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width var(--motion-slow) var(--motion-ease);
}

.progress-inline__bar.is-success {
  background: var(--status-success);
}
.progress-inline__bar.is-running {
  background: var(--status-running);
}
.progress-inline__bar.is-warning {
  background: var(--status-warning);
}
.progress-inline__bar.is-danger {
  background: var(--status-danger);
}

.progress-inline__label {
  font-size: 12px;
  line-height: 16px;
  color: var(--color-text-tertiary);
  font-variant-numeric: tabular-nums;
  min-width: 30px;
}
</style>
