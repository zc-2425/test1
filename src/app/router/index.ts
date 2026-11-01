import { createRouter, createWebHistory } from 'vue-router'
import { routes } from './routes'
import { useAuth } from '@/composables/useAuth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

/**
 * 路由守卫：
 * - 免登录页（目前只有 /login）直接放行；已登录再访问 /login 就送回探索页
 * - 其余路由未登录一律跳登录页，并把原地址塞进 ?redirect=，登录后原路返回
 */
router.beforeEach((to) => {
  const { isAuthenticated } = useAuth()

  if (to.meta.public) {
    if (to.name === 'login' && isAuthenticated.value) {
      return { path: '/explore' }
    }
    return true
  }

  if (!isAuthenticated.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  return true
})

router.afterEach((to) => {
  const title = to.meta.title
  document.title = title ? `${title} · AI 智能体应用开发平台` : 'AI 智能体应用开发平台'
})

export default router
