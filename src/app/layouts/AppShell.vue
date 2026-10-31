<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import ShellSidebar from './ShellSidebar.vue'
import ShellTopbar from './ShellTopbar.vue'

const route = useRoute()
/** 画布页用三栏工作区替代侧栏（原型如此） */
const showSidebar = computed(() => !route.meta.hideSidebar)
</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--full': !showSidebar }">
    <ShellTopbar />
    <div class="app-shell__body">
      <ShellSidebar v-if="showSidebar" />
      <main class="app-shell__main">
        <RouterView v-slot="{ Component }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: var(--color-bg);
}

.app-shell__body {
  display: flex;
  flex: 1 1 auto;
  min-height: 0;
}

.app-shell__main {
  flex: 1 1 auto;
  min-width: 0;
  overflow: auto;
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity var(--motion-fast) var(--motion-ease);
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}
</style>
