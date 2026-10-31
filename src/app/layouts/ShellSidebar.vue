<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { NAV_ITEMS } from '@/app/router/nav'

const route = useRoute()
/** 按路由 meta.navKey 高亮，而不是按菜单文案猜（原型有 2 处高亮错位，这里纠正） */
const activeKey = computed(() => route.meta.navKey ?? '')
</script>

<template>
  <aside class="sidebar">
    <nav class="sidebar__nav" aria-label="主导航">
      <RouterLink
        v-for="item in NAV_ITEMS"
        :key="item.key"
        :to="item.to"
        class="sidebar__item"
        :class="{ 'sidebar__item--active': item.key === activeKey }"
      >
        <i :class="['mdi', item.icon, 'sidebar__icon']" aria-hidden="true" />
        <span class="sidebar__label">{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>

<style scoped>
.sidebar {
  flex: 0 0 auto;
  width: var(--layout-sidebar-width);
  background: var(--color-sidebar-bg);
  border-right: var(--border-width) solid var(--color-sidebar-divider);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar__nav {
  padding: var(--spacing-2) 0;
}

/* 激活态是整行直角紫底白字，不是 M3 药丸 —— 见 docs/04 与录屏实测 */
.sidebar__item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  height: 44px;
  padding: 0 var(--spacing-4);
  border-radius: 0;
  color: var(--color-text-sidebar);
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
  text-decoration: none;
  transition:
    background-color var(--motion-fast) var(--motion-ease),
    color var(--motion-fast) var(--motion-ease);
}

.sidebar__item:hover {
  background: rgba(103, 80, 164, 0.06);
}

.sidebar__item--active,
.sidebar__item--active:hover {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  font-weight: 500;
}

.sidebar__icon {
  font-size: 18px;
  width: 18px;
  line-height: 1;
  flex: 0 0 auto;
  opacity: 0.9;
}

.sidebar__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
