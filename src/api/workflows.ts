/**
 * 工作流接口。字段与后端 SQLModel 保持一致（snake_case）。
 * P5 做列表页时，其余 8 个实体照这个文件复制改字段即可。
 */

import type { PageResult } from '@/types/common'
import { apiGet, apiPost } from './http'

export interface WorkflowDto {
  id: string
  name: string
  description: string
  type: string
  status: string
  node_count: number
  success_rate: number
  last_run_at: string | null
  created_at: string
  updated_at: string
}

export interface ListQuery {
  page?: number
  size?: number
  q?: string
  status?: string
  type?: string
  /** 排序字段名（后端校验，不存在的字段回落到 id） */
  sort?: string
  /** 排序方向，仅 asc/desc 合法 */
  order?: 'asc' | 'desc'
}

export function listWorkflows(query: ListQuery = {}): Promise<PageResult<WorkflowDto>> {
  return apiGet<PageResult<WorkflowDto>>('/workflows', { ...query })
}

export function getWorkflow(id: string): Promise<WorkflowDto> {
  return apiGet<WorkflowDto>(`/workflows/${id}`)
}

export function createWorkflow(payload: Partial<WorkflowDto>): Promise<WorkflowDto> {
  return apiPost<WorkflowDto>('/workflows', payload)
}

export interface RunResult {
  runId: string
  workflowId: string
  workflowName: string
  status: string
  startedAt: string
  durationMs: number
  tokens: { prompt: number; completion: number }
  output: string
  steps: Array<{
    nodeId: string
    nodeType: string
    name: string
    status: string
    durationMs: number
    output?: string
  }>
}

export function runWorkflow(id: string, input = ''): Promise<RunResult> {
  return apiPost<RunResult>(`/workflows/${id}/run`, { input })
}
