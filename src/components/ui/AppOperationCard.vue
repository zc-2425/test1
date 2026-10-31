<script setup lang="ts">
/**
 * 右侧操作卡：详情页右栏的「快速操作 / 数据集操作 / 提供商操作」都是这个形态——
 * 一列图标 + 文案的操作项，最后一个通常是危险操作（删除）。
 */
import type { OperationItem } from './types'

withDefaults(
  defineProps<{
    title?: string
    items: OperationItem[]
    /** 去掉卡片外壳（已有父级卡片时用） */
    bare?: boolean
  }>(),
  { title: '快速操作', bare: false }
)

defineEmits<{ (e: 'action', key: string): void }>()
</script>

<template>
  <div class="op-card" :class="{ 'is-bare': bare }">
    <h3 v-if="title" class="op-card__title">{{ title }}</h3>
    <ul class="op-card__list">
      <li v-for="item in items" :key="item.key">
        <button
          type="button"
          class="op-card__item"
          :class="item.tone === 'danger' ? 'is-danger' : ''"
          :disabled="item.disabled"
          @click="$emit('action', item.key)"
        >
          <i v-if="item.icon" :class="['mdi', item.icon, 'op-card__icon']" aria-hidden="true" />
          <span class="op-card__text">
            <span class="op-card__label">{{ item.label }}</span>
            <span v-if="item.description" class="op-card__desc">{{ item.description }}</span>
          </span>
          <i class="mdi mdi-chevron-right op-card__chevron" aria-hidden="true" />
        </button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.op-card {
  background: var(--color-surface);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-5);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.op-card.is-bare {
  border: 0;
  padding: 0;
  background: transparent;
}

.op-card__title {
  font: var(--font-title-md);
  color: var(--color-text);
}

.op-card__list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.op-card__item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  text-align: left;
  cursor: pointer;
  font-family: inherit;
  transition: background-color var(--motion-fast) var(--motion-ease);
}

.op-card__item:hover:not(:disabled) {
  background: var(--color-surface-low);
}

.op-card__item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.op-card__icon {
  flex: 0 0 auto;
  font-size: 18px;
  color: var(--color-primary);
}

.op-card__item.is-danger .op-card__icon {
  color: var(--status-danger);
}

.op-card__text {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.op-card__label {
  font: var(--font-body-md);
  color: var(--color-text);
}

.op-card__item.is-danger .op-card__label {
  color: var(--status-danger);
}

.op-card__desc {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.op-card__chevron {
  flex: 0 0 auto;
  font-size: 16px;
  color: var(--color-text-tertiary);
}
</style>
