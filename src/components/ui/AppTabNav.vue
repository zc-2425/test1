<script setup lang="ts">
/**
 * 页内 Tab。原型里有两套：
 * 1. underline（下划线）—— Agent 详情的「配置 / 运行历史 / 工具管理」、提示词编辑器；
 * 2. pill（胶囊）—— 模型提供商的「所有提供商 / 已配置 / 可用模型 / 调用统计」。
 */
import type { TabItem } from './types'

const active = defineModel<string>({ required: true })

withDefaults(
  defineProps<{
    items: TabItem[]
    variant?: 'underline' | 'pill'
  }>(),
  { variant: 'underline' }
)

defineEmits<{ (e: 'change', key: string): void }>()
</script>

<template>
  <div class="tab-nav" :class="`is-${variant}`" role="tablist">
    <button
      v-for="item in items"
      :key="item.key"
      type="button"
      role="tab"
      class="tab-nav__item"
      :class="{ 'is-active': item.key === active }"
      :aria-selected="item.key === active"
      @click="
        () => {
          active = item.key
          $emit('change', item.key)
        }
      "
    >
      <span>{{ item.label }}</span>
      <span v-if="item.count !== undefined" class="tab-nav__count">{{ item.count }}</span>
    </button>
  </div>
</template>

<style scoped>
.tab-nav {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  min-width: 0;
}

/* —— 下划线式 —— */
.is-underline {
  border-bottom: var(--border-width) solid var(--color-divider);
  gap: var(--spacing-5);
}

.is-underline .tab-nav__item {
  position: relative;
  height: 40px;
  padding: 0 2px;
  border: 0;
  background: transparent;
  color: var(--color-text-secondary);
  font-family: inherit;
  font-size: 14px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  transition: color var(--motion-fast) var(--motion-ease);
}

.is-underline .tab-nav__item::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 2px;
  background: transparent;
  border-radius: 2px 2px 0 0;
  transition: background-color var(--motion-fast) var(--motion-ease);
}

.is-underline .tab-nav__item:hover {
  color: var(--color-text);
}

.is-underline .tab-nav__item.is-active {
  color: var(--color-primary);
  font-weight: 500;
}

.is-underline .tab-nav__item.is-active::after {
  background: var(--color-primary);
}

/* —— 胶囊式 —— */
.is-pill .tab-nav__item {
  height: 32px;
  padding: 0 var(--spacing-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-secondary);
  font-family: inherit;
  font-size: 13px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  transition:
    background-color var(--motion-fast) var(--motion-ease),
    color var(--motion-fast) var(--motion-ease),
    border-color var(--motion-fast) var(--motion-ease);
}

.is-pill .tab-nav__item:hover {
  border-color: var(--color-primary-light);
  color: var(--color-primary);
}

.is-pill .tab-nav__item.is-active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-text-inverse);
  font-weight: 500;
}

.tab-nav__count {
  font-size: 11px;
  line-height: 16px;
  padding: 0 6px;
  border-radius: var(--radius-full);
  background: var(--color-surface-container);
  color: var(--color-text-secondary);
}

.is-pill .tab-nav__item.is-active .tab-nav__count {
  background: rgba(255, 255, 255, 0.24);
  color: var(--color-text-inverse);
}
</style>
