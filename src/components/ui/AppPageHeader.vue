<script setup lang="ts">
/** 页面标题区：大标题 + 副标题 + 右上操作组。31 个页面里有 20 个用它。 */
withDefaults(
  defineProps<{
    title: string
    subtitle?: string
    /** 列表页标题下方留白略小 */
    compact?: boolean
  }>(),
  { compact: false }
)
</script>

<template>
  <header class="page-header" :class="{ 'page-header--compact': compact }">
    <div class="page-header__text">
      <h1 class="page-header__title">{{ title }}</h1>
      <p v-if="subtitle" class="page-header__subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-5);
}

.page-header--compact {
  margin-bottom: var(--spacing-4);
}

.page-header__text {
  min-width: 0;
}

.page-header__title {
  font: var(--font-headline-sm);
  color: var(--color-text);
}

.page-header__subtitle {
  margin-top: var(--spacing-1);
  font: var(--font-body-md);
  color: var(--color-text-secondary);
  max-width: 760px;
}

.page-header__actions {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}
</style>
