<script setup lang="ts">
/**
 * 按钮：把原型里出现的四种形态收敛成 variant，
 * 避免每个页面各写一套 v-btn 属性（原型里按钮圆角、描边、颜色其实不统一）。
 *
 * primary  实底主色胶囊    —— 「+ 创建新工作流」「保存」
 * secondary 描边胶囊       —— 「运行」「复制」「分享」
 * ghost    纯文字          —— 表格行内、卡片右上
 * danger   危险实底/描边   —— 「删除 Agent」
 */
withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
    size?: 'sm' | 'md'
    /** 图标名（MDI 类名不带 mdi- 前缀也行，这里统一要求带前缀，如 mdi-plus） */
    icon?: string
    /** 图标在文字后 */
    iconAfter?: boolean
    block?: boolean
    loading?: boolean
    disabled?: boolean
    type?: 'button' | 'submit'
  }>(),
  {
    variant: 'primary',
    size: 'md',
    block: false,
    loading: false,
    disabled: false,
    type: 'button'
  }
)

defineEmits<{ (e: 'click', event: MouseEvent): void }>()
</script>

<template>
  <button
    :type="type"
    class="app-btn"
    :class="[`is-${variant}`, `is-${size}`, { 'is-block': block }]"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <span v-if="loading" class="app-btn__spinner" aria-hidden="true" />
    <i v-else-if="icon && !iconAfter" :class="['mdi', icon]" aria-hidden="true" />
    <span class="app-btn__label"><slot /></span>
    <i v-if="icon && iconAfter" :class="['mdi', icon]" aria-hidden="true" />
  </button>
</template>

<style scoped>
.app-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-radius: var(--radius-full);
  border: 1px solid transparent;
  font-family: inherit;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background-color var(--motion-fast) var(--motion-ease),
    border-color var(--motion-fast) var(--motion-ease),
    color var(--motion-fast) var(--motion-ease),
    filter var(--motion-fast) var(--motion-ease);
}

.app-btn.is-md {
  height: 36px;
  padding: 0 var(--spacing-4);
  font-size: 13px;
}

.app-btn.is-sm {
  height: 30px;
  padding: 0 var(--spacing-3);
  font-size: 12px;
}

.app-btn.is-block {
  width: 100%;
}

.app-btn .mdi {
  font-size: 16px;
}

/* 主按钮：实底主色 */
.app-btn.is-primary {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.app-btn.is-primary:hover:not(:disabled) {
  filter: brightness(1.08);
}

/* 次按钮：描边，hover 变浅紫底 */
.app-btn.is-secondary {
  background: transparent;
  border-color: var(--color-border);
  color: var(--color-text);
}

.app-btn.is-secondary:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: rgba(103, 80, 164, 0.04);
}

/* 幽灵按钮 */
.app-btn.is-ghost {
  background: transparent;
  color: var(--color-text-secondary);
}

.app-btn.is-ghost:hover:not(:disabled) {
  background: var(--color-surface-container);
  color: var(--color-primary);
}

/* 危险按钮：描边红，hover 实底 */
.app-btn.is-danger {
  background: transparent;
  border-color: var(--status-danger);
  color: var(--status-danger);
}

.app-btn.is-danger:hover:not(:disabled) {
  background: var(--status-danger);
  color: #fff;
}

.app-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.app-btn__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: app-btn-spin 0.7s linear infinite;
}

@keyframes app-btn-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
