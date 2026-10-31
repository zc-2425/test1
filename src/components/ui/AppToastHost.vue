<script setup lang="ts">
import { dismissToast, useToasts } from '@/composables/useToast'

const { items } = useToasts()

const ICONS: Record<string, string> = {
  success: 'mdi-check-circle',
  error: 'mdi-alert-circle',
  warning: 'mdi-alert',
  info: 'mdi-information'
}
</script>

<template>
  <Teleport to="body">
    <div class="toast-host" aria-live="polite" aria-atomic="false">
      <TransitionGroup name="toast">
        <div v-for="item in items" :key="item.id" class="toast" :class="`is-${item.tone}`" role="status">
          <i :class="['mdi', ICONS[item.tone ?? 'success'], 'toast__icon']" aria-hidden="true" />
          <div class="toast__text">
            <p class="toast__title">{{ item.title }}</p>
            <p v-if="item.description" class="toast__desc">{{ item.description }}</p>
          </div>
          <button type="button" class="toast__close" aria-label="关闭提示" @click="dismissToast(item.id)">
            <i class="mdi mdi-close" aria-hidden="true" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-host {
  position: fixed;
  top: calc(var(--layout-topbar-height) + var(--spacing-2));
  right: var(--spacing-4);
  z-index: 3000;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  min-width: 260px;
  max-width: 380px;
  padding: var(--spacing-3) var(--spacing-3) var(--spacing-3) var(--spacing-4);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-left-width: 3px;
  box-shadow: var(--shadow-card-hover);
  pointer-events: auto;
}

.toast.is-success {
  border-left-color: var(--status-success);
}
.toast.is-error {
  border-left-color: var(--status-danger);
}
.toast.is-warning {
  border-left-color: var(--status-warning);
}
.toast.is-info {
  border-left-color: var(--status-info);
}

.toast__icon {
  font-size: 18px;
  margin-top: 1px;
  flex: 0 0 auto;
}

.toast.is-success .toast__icon {
  color: var(--status-success);
}
.toast.is-error .toast__icon {
  color: var(--status-danger);
}
.toast.is-warning .toast__icon {
  color: var(--status-warning);
}
.toast.is-info .toast__icon {
  color: var(--status-info);
}

.toast__text {
  flex: 1 1 auto;
  min-width: 0;
}

.toast__title {
  font: var(--font-body-md);
  color: var(--color-text);
}

.toast__desc {
  margin-top: 2px;
  font: var(--font-label-sm);
  color: var(--color-text-secondary);
}

.toast__close {
  flex: 0 0 auto;
  width: 22px;
  height: 22px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: 14px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.toast__close:hover {
  background: var(--color-surface-container);
}

/* 进出场：右侧滑入 + 淡出 */
.toast-enter-active,
.toast-leave-active {
  transition:
    opacity var(--motion-base) var(--motion-ease),
    transform var(--motion-base) var(--motion-ease);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(16px);
}

.toast-move {
  transition: transform var(--motion-base) var(--motion-ease);
}
</style>
