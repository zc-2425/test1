<script setup lang="ts">
import { useRouter } from 'vue-router'

/**
 * 详情页页头：返回箭头 + 图标/头像 + 标题 + 副标题 + 状态 + 操作组。
 * 6 个详情页（Agent / 知识库 / 数据集 / 工具 / 厂商 / 应用）同构，抽出来避免各写一套。
 *
 * 注意：原型顶栏**没有面包屑**，详情页返回全靠页头这个箭头（部分详情页原型连箭头都漏了），
 * 所以这里默认显示返回按钮。
 */
const props = withDefaults(
  defineProps<{
    title: string
    subtitle?: string
    /** 图标名，如 mdi-robot-outline；与 avatarText 二选一 */
    icon?: string
    /** 头像内文字（取名称首字），优先于 icon */
    avatarText?: string
    /** 返回目标路由；不传则 router.back() */
    backTo?: string
    showBack?: boolean
  }>(),
  { showBack: true }
)

const router = useRouter()

function goBack(): void {
  if (props.backTo) void router.push(props.backTo)
  else router.back()
}
</script>

<template>
  <header class="detail-header">
    <button
      v-if="showBack"
      type="button"
      class="detail-header__back"
      aria-label="返回"
      @click="goBack"
    >
      <i class="mdi mdi-arrow-left" aria-hidden="true" />
    </button>

    <span v-if="avatarText || icon" class="detail-header__avatar">
      <template v-if="avatarText">{{ avatarText }}</template>
      <i v-else :class="['mdi', icon]" aria-hidden="true" />
    </span>

    <div class="detail-header__text">
      <h1 class="detail-header__title">{{ title }}</h1>
      <p v-if="subtitle" class="detail-header__subtitle">{{ subtitle }}</p>
    </div>

    <div class="detail-header__status">
      <slot name="status" />
    </div>

    <div class="detail-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.detail-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-5);
  min-width: 0;
}

.detail-header__back {
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 20px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.detail-header__back:hover {
  background: var(--color-surface-container);
  color: var(--color-primary);
}

.detail-header__avatar {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--avatar-lg);
  height: var(--avatar-lg);
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #8b78e6 0%, #6b4fa8 100%);
  color: #fff;
  font-size: 18px;
  font-weight: 500;
}

.detail-header__text {
  min-width: 0;
  flex: 1 1 auto;
}

.detail-header__title {
  font: var(--font-title-lg);
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-header__subtitle {
  margin-top: 2px;
  font: var(--font-body-sm);
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-header__status {
  flex: 0 0 auto;
}

.detail-header__actions {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}
</style>
