<script setup lang="ts">
/**
 * 右侧抽屉。原型 62 页里一次都没画过抽屉（录屏里 0 个），
 * 但「新建应用」「添加提供商」「工具运行」「Agent 运行调试」这些操作塞进抽屉比弹窗合适，
 * 所以按 docs/01 的需求清单补上，宽度取 560。
 */
const open = defineModel<boolean>({ default: false })

withDefaults(
  defineProps<{
    title?: string
    subtitle?: string
    width?: number | string
    /** 点遮罩不关闭 */
    persistent?: boolean
  }>(),
  { width: 560, persistent: false }
)
</script>

<template>
  <v-navigation-drawer
    v-model="open"
    location="right"
    temporary
    :width="width"
    :scrim="true"
    class="app-drawer"
  >
    <header v-if="title || $slots.header" class="app-drawer__head">
      <div class="app-drawer__heading">
        <slot name="header">
          <h2 class="app-drawer__title">{{ title }}</h2>
          <p v-if="subtitle" class="app-drawer__subtitle">{{ subtitle }}</p>
        </slot>
      </div>
      <button
        type="button"
        class="app-drawer__close"
        aria-label="关闭"
        @click="open = false"
      >
        <i class="mdi mdi-close" aria-hidden="true" />
      </button>
    </header>

    <div class="app-drawer__body">
      <slot />
    </div>

    <footer v-if="$slots.footer" class="app-drawer__foot">
      <slot name="footer" />
    </footer>
  </v-navigation-drawer>
</template>

<style scoped>
.app-drawer {
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-left: var(--border-width) solid var(--color-border);
  /* 抽屉从顶栏下方开始，而不是盖住顶栏（原型没有抽屉，这里按桌面端习惯处理） */
  top: var(--layout-topbar-height);
  height: calc(100% - var(--layout-topbar-height));
}

.app-drawer__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-4);
  padding: var(--spacing-5);
  border-bottom: var(--border-width) solid var(--color-divider);
}

.app-drawer__heading {
  min-width: 0;
}

.app-drawer__title {
  font: var(--font-title-lg);
  color: var(--color-text);
}

.app-drawer__subtitle {
  margin-top: var(--spacing-1);
  font: var(--font-body-sm);
  color: var(--color-text-secondary);
}

.app-drawer__close {
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

.app-drawer__close:hover {
  background: var(--color-surface-container);
}

.app-drawer__body {
  flex: 1 1 auto;
  overflow: auto;
  padding: var(--spacing-5);
}

.app-drawer__foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-5);
  border-top: var(--border-width) solid var(--color-divider);
}
</style>
