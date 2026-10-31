<script setup lang="ts">
/**
 * 多行文本。agent 的系统提示词、工具描述、工作流节点配置都用它。
 * autoGrow 打开时随内容长高（原型里系统提示词框是固定高度，这里默认固定）。
 */
defineOptions({ inheritAttrs: false })

const model = defineModel<string>({ default: '' })

withDefaults(
  defineProps<{
    label?: string
    placeholder?: string
    hint?: string
    error?: string
    required?: boolean
    disabled?: boolean
    readonly?: boolean
    rows?: number
    maxRows?: number
    autoGrow?: boolean
    /** 显示字数统计：传 true 或具体上限（提示词类输入有用） */
    counter?: number | true
  }>(),
  { rows: 3, autoGrow: false }
)
</script>

<template>
  <div class="app-textarea">
    <label v-if="label" class="app-textarea__label">
      {{ label }}
      <span v-if="required" class="app-textarea__required">*</span>
    </label>
    <v-textarea
      v-model="model"
      v-bind="$attrs"
      variant="outlined"
      density="comfortable"
      :rows="rows"
      :max-rows="maxRows"
      :auto-grow="autoGrow"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      :error-messages="error || undefined"
      :hint="hint"
      :persistent-hint="!!hint"
      :counter="counter"
      hide-details="auto"
      color="primary"
    />
  </div>
</template>

<style scoped>
.app-textarea {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.app-textarea__label {
  font-size: 12px;
  line-height: 16px;
  color: var(--color-text-secondary);
}

.app-textarea__required {
  color: var(--status-danger);
  margin-left: 2px;
}

.app-textarea :deep(.v-field) {
  border-radius: var(--radius-sm);
}

.app-textarea :deep(textarea) {
  font-size: 13px;
  line-height: 20px;
}

.app-textarea :deep(.v-messages__message) {
  font-size: 12px;
  color: var(--color-text-tertiary);
}
</style>
