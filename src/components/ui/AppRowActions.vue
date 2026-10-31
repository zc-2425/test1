<script setup lang="ts">
/**
 * 表格行内操作：▶ 运行 + ⋮ 更多。
 * 原型 62 页的行内操作只有这两个图标，且 ⋮ 从未被点开过（内容是我们补的）。
 */
import type { RowAction } from './types'

withDefaults(
  defineProps<{
    actions: RowAction[]
    /** 显示 ▶ 运行按钮 */
    showRun?: boolean
    runTitle?: string
  }>(),
  { showRun: true, runTitle: '运行' }
)

defineEmits<{ (e: 'action', key: string): void }>()
</script>

<template>
  <div class="row-actions">
    <button
      v-if="showRun"
      type="button"
      class="row-actions__btn"
      :title="runTitle"
      :aria-label="runTitle"
      @click.stop="$emit('action', 'run')"
    >
      <i class="mdi mdi-play" aria-hidden="true" />
    </button>

    <v-menu location="bottom end" offset="4">
      <template #activator="{ props }">
        <button
          v-bind="props"
          type="button"
          class="row-actions__btn"
          title="更多"
          aria-label="更多操作"
          @click.stop
        >
          <i class="mdi mdi-dots-vertical" aria-hidden="true" />
        </button>
      </template>
      <v-list density="compact" min-width="140">
        <v-list-item
          v-for="item in actions"
          :key="item.key"
          :title="item.label"
          :prepend-icon="item.icon"
          :base-color="item.tone === 'danger' ? 'error' : undefined"
          @click="$emit('action', item.key)"
        />
      </v-list>
    </v-menu>
  </div>
</template>

<style scoped>
.row-actions {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.row-actions__btn {
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 17px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition:
    background-color var(--motion-fast) var(--motion-ease),
    color var(--motion-fast) var(--motion-ease);
}

.row-actions__btn:hover {
  background: var(--color-surface-container);
  color: var(--color-primary);
}
</style>
