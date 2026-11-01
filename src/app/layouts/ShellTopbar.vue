<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { toast } from '@/composables/useToast'

const router = useRouter()
const { user, logout: clearSession } = useAuth()

/** 没有会话时（理论上会被守卫挡住）退化成 Admin，避免顶部出现空白 */
const displayName = computed(() => user.value?.displayName ?? 'Admin')
const roleLabel = computed(() => {
  const role = user.value?.role
  if (role === 'admin') return '管理员'
  if (role === 'developer') return '开发者'
  if (role === 'viewer') return '只读'
  return ''
})

function logout() {
  const name = displayName.value
  clearSession()
  toast('已退出登录', { tone: 'info', description: name })
  void router.push('/login')
}
</script>

<template>
  <header class="topbar">
    <div class="topbar__brand">
      <span class="topbar__logo">
        <i class="mdi mdi-robot-happy-outline" aria-hidden="true" />
      </span>
      <span class="topbar__title">AI 智能体应用开发平台</span>
    </div>

    <div class="topbar__actions">
      <v-menu location="bottom end" offset="4">
        <template #activator="{ props }">
          <button v-bind="props" type="button" class="topbar__user">
            <span class="topbar__avatar">
              <i class="mdi mdi-account" aria-hidden="true" />
            </span>
            <span class="topbar__user-name">{{ displayName }}</span>
            <i class="mdi mdi-chevron-down topbar__caret" aria-hidden="true" />
          </button>
        </template>
        <v-list density="compact" min-width="160">
          <v-list-item prepend-icon="mdi-account-outline" title="个人信息" :subtitle="roleLabel" />
          <v-list-item prepend-icon="mdi-cog-outline" title="设置" />
          <v-divider class="my-1" />
          <v-list-item prepend-icon="mdi-logout" title="退出登录" @click="logout" />
        </v-list>
      </v-menu>

      <button type="button" class="topbar__icon-btn" aria-label="通知">
        <i class="mdi mdi-bell-outline" aria-hidden="true" />
        <span class="topbar__dot" />
      </button>

      <button type="button" class="topbar__icon-btn" aria-label="退出登录" @click="logout">
        <i class="mdi mdi-power" aria-hidden="true" />
      </button>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  flex: 0 0 auto;
  height: var(--layout-topbar-height);
  background: var(--color-primary);
  color: var(--color-text-inverse);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-4) 0 var(--spacing-4);
}

.topbar__brand {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  min-width: 0;
}

.topbar__logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.16);
  font-size: 18px;
}

.topbar__title {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.2px;
  white-space: nowrap;
}

.topbar__actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.topbar__user {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  height: 34px;
  padding: 0 var(--spacing-2) 0 var(--spacing-1);
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-inverse);
  font-size: 13px;
  cursor: pointer;
  transition: background-color var(--motion-fast) var(--motion-ease);
}

.topbar__user:hover {
  background: rgba(255, 255, 255, 0.12);
}

.topbar__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  color: var(--color-primary);
  font-size: 16px;
}

.topbar__caret {
  font-size: 16px;
  opacity: 0.85;
}

.topbar__icon-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text-inverse);
  font-size: 20px;
  cursor: pointer;
  transition: background-color var(--motion-fast) var(--motion-ease);
}

.topbar__icon-btn:hover {
  background: rgba(255, 255, 255, 0.12);
}

.topbar__dot {
  position: absolute;
  top: 7px;
  right: 8px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ff5252;
  border: 1px solid var(--color-primary);
}
</style>
