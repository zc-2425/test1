<script setup lang="ts">
/**
 * 空状态 / 无结果 / 从未运行。原型一次都没画过空态，
 * 但 7 个列表页 + 5 个详情页都会遇到，必须补（见 docs/01「必须显式实现的状态而非页面」）。
 */
withDefaults(
  defineProps<{
    icon?: string
    title?: string
    description?: string
    /** 纵向留白，表格内嵌时用小号 */
    size?: 'sm' | 'md'
  }>(),
  { icon: 'mdi-inbox-outline', title: '暂无数据', size: 'md' }
)
</script>

<template>
  <div class="empty-state" :class="`is-${size}`">
    <span class="empty-state__icon">
      <i :class="['mdi', icon]" aria-hidden="true" />
    </span>
    <p class="empty-state__title">{{ title }}</p>
    <p v-if="description" class="empty-state__desc">{{ description }}</p>
    <div v-if="$slots.action" class="empty-state__action">
      <slot name="action" />
    </div>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--spacing-10) var(--spacing-4);
  gap: var(--spacing-2);
}

.empty-state.is-sm {
  padding: var(--spacing-6) var(--spacing-3);
}

.empty-state__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--color-surface-container);
  color: var(--color-text-tertiary);
  font-size: 26px;
  margin-bottom: var(--spacing-1);
}

.empty-state.is-sm .empty-state__icon {
  width: 40px;
  height: 40px;
  font-size: 20px;
}

.empty-state__title {
  font: var(--font-title-md);
  color: var(--color-text);
}

.empty-state.is-sm .empty-state__title {
  font: var(--font-body-md);
}

.empty-state__desc {
  font: var(--font-body-sm);
  color: var(--color-text-tertiary);
  max-width: 360px;
}

.empty-state__action {
  margin-top: var(--spacing-2);
}
</style>
