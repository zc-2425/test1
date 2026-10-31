<script setup lang="ts">
/**
 * 居中模态。原型里确认出现的两个弹窗（「创建工作流」「运行工作流」）以及
 * 告警中心、LLMOps 设置都是这个形态：遮罩 0.4、圆角 16、宽 560。
 *
 * 用 v-dialog 做底座：焦点陷阱、Esc 关闭、滚动锁定、遮罩点击都已实现，
 * 自己重写一遍只会漏掉无障碍细节。
 */
const open = defineModel<boolean>({ default: false })

withDefaults(
  defineProps<{
    title?: string
    subtitle?: string
    /** 数字按 px 处理，也接受 '720px' */
    maxWidth?: number | string
    /** 点遮罩不关闭 */
    persistent?: boolean
    hideClose?: boolean
  }>(),
  { maxWidth: 560, persistent: false, hideClose: false }
)
</script>

<template>
  <v-dialog v-model="open" :max-width="maxWidth" :persistent="persistent" scrim="rgba(0, 0, 0, 0.4)">
    <v-card class="app-modal" elevation="0" rounded="lg">
      <header v-if="title || $slots.header" class="app-modal__head">
        <div class="app-modal__heading">
          <slot name="header">
            <h2 class="app-modal__title">{{ title }}</h2>
            <p v-if="subtitle" class="app-modal__subtitle">{{ subtitle }}</p>
          </slot>
        </div>
        <button
          v-if="!hideClose"
          type="button"
          class="app-modal__close"
          aria-label="关闭"
          @click="open = false"
        >
          <i class="mdi mdi-close" aria-hidden="true" />
        </button>
      </header>

      <div class="app-modal__body">
        <slot />
      </div>

      <footer v-if="$slots.footer" class="app-modal__foot">
        <slot name="footer" />
      </footer>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.app-modal {
  background: var(--color-surface);
  border: var(--border-width) solid var(--color-border);
  max-height: 86vh;
  display: flex;
  flex-direction: column;
}

.app-modal__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-4);
  padding: var(--spacing-5) var(--spacing-5) var(--spacing-3);
}

.app-modal__heading {
  min-width: 0;
}

.app-modal__title {
  font: var(--font-title-lg);
  color: var(--color-text);
}

.app-modal__subtitle {
  margin-top: var(--spacing-1);
  font: var(--font-body-sm);
  color: var(--color-text-secondary);
}

.app-modal__close {
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 18px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.app-modal__close:hover {
  background: var(--color-surface-container);
}

.app-modal__body {
  padding: 0 var(--spacing-5) var(--spacing-5);
  overflow: auto;
  flex: 1 1 auto;
}

.app-modal__foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-5);
  border-top: var(--border-width) solid var(--color-divider);
}
</style>
