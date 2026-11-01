/**
 * 模型厂商的运维接口（真实连通性测试）。
 * 通用 CRUD 在 resources.ts，这里只放「测试连接」这一个动作。
 */

import { apiPost } from './http'

export type ProviderTestResult = {
  ok: boolean
  latencyMs: number
  message: string
  /** 该厂商是否在「支持真实测试」的名单里 */
  supported?: boolean
  /** 缺少 API Key */
  needsKey?: boolean
  /** 应该把 Key 写进哪个环境变量，如 APP_DEEPSEEK_API_KEY */
  envVar?: string | null
  model?: string
}

export function testProvider(id: string): Promise<ProviderTestResult> {
  return apiPost<ProviderTestResult>(`/providers/${id}/test`)
}
