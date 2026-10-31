<script setup lang="ts">
import { computed } from 'vue'

/**
 * 滑块：LLM 节点面板的「温度 0.7」、知识检索的「相似度阈值 0.75」。
 * 原型的数字框其实更适合滑块——这类 0~1 的连续参数用输入框体验很差，已在 docs 里标注为需补齐项。
 */
const model = defineModel<number>({ default: 0 })

const props = withDefaults(
  defineProps<{
    label?: string
    min?: number
    max?: number
    step?: number
    disabled?: boolean
    /** 数值后缀，如 '' / '%' */
    suffix?: string
    /** 右侧附注，如「推荐 0.7」 */
    hint?: string
  }>(),
  { min: 0, max: 1, step: 0.1, suffix: '' }
)

const displayValue = computed(() => {
  const value = Number(model.value ?? 0)
  // 0.1 步长时会浮出 0.30000000000000004，按步长精度取整
  const decimals = String(props.step).includes('.') ? String(props.step).split('.')[1].length : 0
  return value.toFixed(decimals)
})

</script>

<template>
  <div class="app-slider">
    <div class="app-slider__head">
      <label v-if="label" class="app-slider__label">{{ label }}</label>
      <span class="app-slider__value">{{ displayValue }}{{ suffix }}</span>
    </div>
    <v-slider
      v-model="model"
      :min="min"
      :max="max"
      :step="step"
      :disabled="disabled"

      color="primary"
      track-color="surface-variant"
      density="compact"
      hide-details
    />
    <span v-if="hint" class="app-slider__hint">{{ hint }}</span>
  </div>
</template>

<style scoped>
.app-slider {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.app-slider__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--spacing-3);
}

.app-slider__label {
  font-size: 12px;
  line-height: 16px;
  color: var(--color-text-secondary);
}

.app-slider__value {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-primary);
  font-variant-numeric: tabular-nums;
}

.app-slider :deep(.v-slider) {
  margin: 0;
}

.app-slider__hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
}
</style>