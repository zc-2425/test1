/**
 * 认证接口。
 * 后端练手版签发的是 `dev-<username>`，但前端只当它是 opaque token ——
 * 换成 JWT 时这里一行都不用改。
 */

import { apiGet, apiPost } from './http'

export type AuthUser = {
  id: string
  username: string
  displayName: string
  email: string
  role: string
}

export type LoginResponse = {
  token: string
  user: AuthUser
}

export function login(identifier: string, password: string): Promise<LoginResponse> {
  return apiPost<LoginResponse>('/auth/login', { username: identifier, password })
}

export function fetchMe(token: string): Promise<AuthUser> {
  return apiGet<AuthUser>('/auth/me', undefined, {
    headers: { Authorization: `Bearer ${token}` }
  })
}
