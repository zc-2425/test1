import { createRouter, createWebHistory } from 'vue-router'
import { routes } from './routes'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.afterEach((to) => {
  const title = to.meta.title
  document.title = title ? `${title} · AI 智能体应用开发平台` : 'AI 智能体应用开发平台'
})

export default router
