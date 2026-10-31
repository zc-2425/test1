<script setup lang="ts">
/**
 * 筛选条：列表页统一结构 —— 左侧搜索 + 若干下拉，右侧操作按钮。
 * 原型 62 页里**一个筛选条都没有**（0 个搜索框），这是必须补的交互；
 * 把它做成固定结构，7 个列表页的筛选条就不会各长各样。
 */
withDefaults(
  defineProps<{
    /** 结果数量提示，如「共 8 条」 */
    summary?: string
    /** 是否吸顶（长列表滚动时保持可见） */
    sticky?: boolean
  }>(),
  { sticky: false }
)
</script>

<template>
  <div class="filter-bar" :class="{ 'is-sticky': sticky }">
    <div class="filter-bar__main">
      <slot />
    </div>
    <div class="filter-bar__side">
      <span v-if="summary" class="filter-bar__summary">{{ summary }}</span>
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  flex-wrap: wrap;
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: var(--border-width) solid var(--color-divider);
  background: var(--color-surface);
}

.filter-bar.is-sticky {
  position: sticky;
  top: 0;
  z-index: 2;
}

.filter-bar__main {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
  min-width: 0;
}

.filter-bar__side {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex: 0 0 auto;
}

.filter-bar__summary {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}
</style>
