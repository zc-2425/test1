import { computed, ref } from 'vue'
import { ApiError } from '@/api/http'
import { fetchMe, login as loginApi, type AuthUser } from '@/api/auth'

/**
 * 认证状态。
 *
 * 用模块级 ref 而不是 Pinia：路由守卫需要在 pinia 安装前就能读到状态，
 * 而且这里只有「token + user + 三个方法」，多一层 store 不划算。
 *
 * 持久化：勾选「记住我」写 localStorage（关浏览器还在），否则写 sessionStorage（关标签页即失效）。
 */

const STORAGE_KEY = 'aiap:auth'

type StoredSession = { token: string; user: AuthUser }

const token = ref<string | null>(null)
const user = ref<AuthUser | null>(null)

function readFrom(storage: Storage): StoredSession | null {
  try {
    const raw = storage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed: unknown = JSON.parse(raw)
    if (
      parsed &&
      typeof parsed === 'object' &&
      'token' in parsed &&
      'user' in parsed &&
      typeof (parsed as StoredSession).token === 'string'
    ) {
      return parsed as StoredSession
    }
    return null
  } catch {
    return null
  }
}

function writeTo(storage: Storage, session: StoredSession): void {
  try {
    storage.setItem(STORAGE_KEY, JSON.stringify(session))
  } catch {
    /* 隐私模式写入失败，忽略 */
  }
}

function clearStorages(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY)
    window.sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    /* 忽略 */
  }
}

// 同步恢复：路由守卫第一次判断时就必须有结果，所以不能等异步
const restored = readFrom(window.localStorage) ?? readFrom(window.sessionStorage)
if (restored) {
  token.value = restored.token
  user.value = restored.user
}

export function useAuth() {
  const isAuthenticated = computed(() => Boolean(token.value))

  async function login(identifier: string, password: string, remember = true): Promise<void> {
    const result = await loginApi(identifier.trim(), password)
    token.value = result.token
    user.value = result.user
    clearStorages()
    writeTo(remember ? window.localStorage : window.sessionStorage, {
      token: result.token,
      user: result.user
    })
  }

  function logout(): void {
    token.value = null
    user.value = null
    clearStorages()
  }

  /**
   * 启动时后台校验一次会话：只有明确 401 才登出。
   * 网络错误（后端没起来）不清状态，否则开发时一重启后端就被踢回登录页。
   */
  async function revalidate(): Promise<void> {
    if (!token.value) return
    try {
      user.value = await fetchMe(token.value)
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 401) logout()
    }
  }

  return { token, user, isAuthenticated, login, logout, revalidate }
}
