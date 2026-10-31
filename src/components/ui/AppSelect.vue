<script setup lang="ts">
import { computed } from 'vue'

type SelectItem = string | { title: string; value: string | number }

/**
 * 下拉选择：包 v-select。支持纯字符串数组与 {title,value} 两种 items 形态，
 * 避免每个页面都手写 item-title / item-value。
 */
defineOptions({ inheritAttrs: false })

const model = defineModel<string | number | string[] | number[] | null>()

const props = withDefaults(
  defineProps<{
    label?: string
    items: SelectItem[]
    placeholder?: string
    hint?: string
    error?: string
    required?: boolean
    disabled?: boolean
    multiple?: boolean
    clearable?: boolean
    dense?: boolean
  }>(),
  { dense: false, multiple: false, clearable: false }
)

const normalized = computed(() =>
  props.items.map((item) =>
    typeof item === 'string' ? { title: item, value: item } : { title: item.title, value: item.value }
  )
)
</script>

<template>
  <div class="app-select" :class="{ 'is-dense': dense }">
    <label v-if="label" class="app-select__label">
      {{ label }}
      <span v-if="required" class="app-select__required">*</span>
    </label>
    <v-select
      v-model="model"
      v-bind="$attrs"
      :items="normalized"
      :variant="'outlined'"
      :density="dense ? 'compact' : 'comfortable'"
      :multiple="multiple"
      :clearable="clearable"
      :disabled="disabled"
      :placeholder="placeholder"
      :error-messages="error || undefined"
      :hint="hint"
      :persistent-hint="!!hint"
      hide-details="auto"
      color="primary"
    >

      <template v-for="(_, name) in $slots" #[name]="slotProps">
        <slot :name="name" v-bind="slotProps ?? {}" />
      </template>
    </v-select>
  </div>
</template>

<style scoped>
.app-select {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.app-select__label {
  font-size: 12px;
  line-height: 16px;
  color: var(--color-text-secondary);
}

.app-select__required {
  color: var(--status-danger);
  margin-left: 2px;
}

.app-select :deep(.v-field) {
  border-radius: var(--radius-sm);
}

.app-select :deep(.v-field__input) {
  font-size: 13px;
  min-height: 40px;
}

.app-select.is-dense :deep(.v-field__input) {
  min-height: 34px;
  font-size: 12.5px;
}

.app-select :deep(.v-messages__message) {
  font-size: 12px;
  color: var(--color-text-tertiary);
}
</style>
