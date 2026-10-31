/**
 * 工作流专属接口（通用 CRUD 在 resources.ts，这里只放工作流独有的「运行」）。
 * 保留 listWorkflows / WorkflowDto 的旧导出，避免已有页面改动引用路径。
 */

import { apiPost } from './http'
import { workflowsApi } from './resources'
import type { ListQuery, WorkflowDto } from './types'

export type { ListQuery, WorkflowDto }
export { workflowsApi }

export const listWorkflows = workflowsApi.list
export const getWorkflow = workflowsApi.get
export const createWorkflow = workflowsApi.create

export interface RunStep {
  nodeId: string
  nodeType: string
  name: string
  status: string
  durationMs: number
  output?: string
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
  steps: RunStep[]
}

export function runWorkflow(id: string, input = ''): Promise<RunResult> {
  return apiPost<RunResult>(`/workflows/${id}/run`, { input })
}
