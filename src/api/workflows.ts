/**
 * 工作流专属接口（通用 CRUD 在 resources.ts，这里放工作流独有的画布图与运行）。
 * R4 起节点和连线真的落库了：打开画布读 GET /graph，保存写 PUT /graph。
 */

import { apiGet, apiPost, apiPut } from './http'
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
  mode?: string | null
}

export interface RunCitation {
  chunkId: string
  docId: string
  docName: string
  position: number
  score: number
  preview: string
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
  citations?: RunCitation[]
  conversationId?: string
}

export function runWorkflow(id: string, input = ''): Promise<RunResult> {
  return apiPost<RunResult>(`/workflows/${id}/run`, { input })
}

/* ---------------- 画布图 ---------------- */

export interface GraphNodeDto {
  id: string
  type: string
  name: string
  x: number
  y: number
  config: Record<string, unknown>
}

export interface GraphEdgeDto {
  id: string
  from: string
  to: string
  label: string
}

export interface GraphDto {
  workflowId: string
  nodes: GraphNodeDto[]
  edges: GraphEdgeDto[]
}

export function getWorkflowGraph(id: string): Promise<GraphDto> {
  return apiGet<GraphDto>(`/workflows/${id}/graph`)
}

export function saveWorkflowGraph(
  id: string,
  graph: { nodes: Array<Omit<GraphNodeDto, 'name'> & { name?: string }>; edges: GraphEdgeDto[] }
): Promise<{ nodes: number; edges: number }> {
  return apiPut<{ nodes: number; edges: number }>(`/workflows/${id}/graph`, graph)
}
