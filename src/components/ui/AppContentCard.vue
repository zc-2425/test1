<script setup lang="ts">
/** 圆角描边容器。列表页包表格、详情页包信息块、LLMOps 包图表都用它。 */
withDefaults(
  defineProps<{
    title?: string
    subtitle?: string
    /** 去掉内边距（表格需要贴边） */
    flush?: boolean
    /** 紧凑内边距，用于详情页右侧操作卡 */
    dense?: boolean
  }>(),
  { flush: false, dense: false }
)
</script>

<template>
  <section class="content-card" :class="{ 'content-card--flush': flush, 'content-card--dense': dense }">
    <header v-if="title || $slots.header || $slots.actions" class="content-card__header">
      <div class="content-card__heading">
        <h2 v-if="title" class="content-card__title">{{ title }}</h2>
        <p v-if="subtitle" class="content-card__subtitle">{{ subtitle }}</p>
        <slot name="header" />
      </div>
      <div v-if="$slots.actions" class="content-card__actions">
        <slot name="actions" />
      </div>
    </header>

    <div class="content-card__body">
      <slot />
    </div>

    <footer v-if="$slots.footer" class="content-card__footer">
      <slot name="footer" />
    </footer>
  </section>
</template>

<style scoped>
.content-card {
  background: var(--color-surface);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.content-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-4);
  padding: var(--spacing-5) var(--spacing-5) 0;
}

.content-card__title {
  font: var(--font-title-md);
  color: var(--color-text);
}

.content-card__subtitle {
  margin-top: var(--spacing-1);
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.content-card__actions {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.content-card__body {
  padding: var(--spacing-5);
  min-width: 0;
}

.content-card--flush .content-card__body {
  padding: 0;
}

.content-card--flush .content-card__header {
  padding: var(--spacing-4) var(--spacing-4) var(--spacing-3);
}

.content-card--dense .content-card__body {
  padding: var(--spacing-4);
}

.content-card__footer {
  border-top: var(--border-width) solid var(--color-divider);
  padding: var(--spacing-3) var(--spacing-5);
}
</style>
