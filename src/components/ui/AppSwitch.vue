<script setup lang="ts">
/**
 * 开关：模型厂商卡的启用开关、Agent 的记忆开关都用它。
 * 视觉用 Vuetify 的 inset 轨道（M3 长条），主题里已设 color=primary。
 */
const model = defineModel<boolean>({ default: false })

withDefaults(
  defineProps<{
    label?: string
    description?: string
    disabled?: boolean
    /** 轨道右侧显示「已启用 / 已停用」 */
    showState?: boolean
    trueText?: string
    falseText?: string
  }>(),
  { showState: false, trueText: '已启用', falseText: '已停用' }
)
</script>

<template>
  <div class="app-switch" :class="{ 'is-disabled': disabled }">
    <div class="app-switch__text">
      <span v-if="label" class="app-switch__label">{{ label }}</span>
      <span v-if="description" class="app-switch__desc">{{ description }}</span>
    </div>
    <div class="app-switch__control">
      <span v-if="showState" class="app-switch__state">{{
        model ? trueText : falseText
      }}</span>
      <v-switch v-model="model" :disabled="disabled" color="primary" inset hide-details />
    </div>
  </div>
</template>

<style scoped>
.app-switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-4);
  min-width: 0;
}

.app-switch.is-disabled {
  opacity: 0.6;
}

.app-switch__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.app-switch__label {
  font: var(--font-body-md);
  color: var(--color-text);
}

.app-switch__desc {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.app-switch__control {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex: 0 0 auto;
}

.app-switch__state {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.app-switch :deep(.v-switch) {
  flex: 0 0 auto;
}

.app-switch :deep(.v-switch .v-selection-control) {
  min-height: 32px;
}
</style>
