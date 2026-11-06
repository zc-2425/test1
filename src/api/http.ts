/**
 * 接口层唯一出口（P12 的「可插拔」就靠这一层）。
 *
 * 约定：
 * 1. 浏览器只请求同源 `/api/...`，由 Vite 代理到 FastAPI（见 vite.config.ts），不存在跨域；
 * 2. 后端字段是 snake_case，前端 DTO 保持同名，先不做 camelCase 映射——
 *    多一层映射就多一处出错点，等真有第二个消费方再引入；
 * 3. 错误统一抛 ApiError，页面用 try/catch 或 useAsyncData 处理。
 */

const BASE = import.meta.env.VITE_API_BASE ?? '/api'

export class ApiError extends Error {
  readonly status: number
  readonly detail: unknown

  constructor(status: number, message: string, detail?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

type Query = Record<string, string | number | boolean | null | undefined>

function buildQuery(params?: Query): string {
  if (!params) return ''
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    search.append(key, String(value))
  }
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

async function request<T>(path: string, init: RequestInit & { params?: Query } = {}): Promise<T> {
  const { params, headers, ...rest } = init
  const url = `${BASE}${path}${buildQuery(params)}`

  let response: Response
  try {
    response = await fetch(url, {
      ...rest,
      headers: { Accept: 'application/json', ...(headers ?? {}) }
    })
  } catch (cause) {
    throw new ApiError(0, `网络请求失败：${String(cause)}`)
  }

  if (response.status === 204) return undefined as T

  const text = await response.text()
  const payload = text ? safeJson(text) : null

  if (!response.ok) {
    const detail = (payload as { detail?: unknown } | null)?.detail
    const message =
      typeof detail === 'string' ? detail : `请求失败（HTTP ${response.status}）`
    throw new ApiError(response.status, message, detail)
  }

  return payload as T
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export function apiGet<T>(path: string, params?: Query, init?: RequestInit): Promise<T> {
  return request<T>(path, { method: 'GET', params, ...init })
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body)
  })
}

export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
}

export function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
}

export function apiDelete(path: string): Promise<void> {
  return request<void>(path, { method: 'DELETE' })
}
