/**
 * 资源 API 工厂。
 *
 * 9 个实体的 CRUD 形状完全一致（后端也是同一个 CRUD 工厂生成的），
 * 所以前端也只写一份；每个实体的差异仅在于泛型。
 *
 * 用法：
 *   const page = await workflowsApi.list({ page: 1, size: 10, q: '客服' })
 *   await agentsApi.remove('agt-001')
 */

import type { PageResult } from '@/types/common'
import { apiDelete, apiGet, apiPatch, apiPost } from './http'
import type {
  AgentDto,
  AppDto,
  DatasetDto,
  KnowledgeBaseDto,
  ListQuery,
  PluginDto,
  PromptDto,
  ProviderDto,
  ToolDto,
  WorkflowDto
} from './types'

export interface ResourceApi<T> {
  /** 分页列表：支持关键字、状态、类型筛选与排序 */
  list(query?: ListQuery): Promise<PageResult<T>>
  get(id: string): Promise<T>
  create(payload: Partial<T>): Promise<T>
  update(id: string, payload: Partial<T>): Promise<T>
  remove(id: string): Promise<void>
}

export function createResource<T>(path: string): ResourceApi<T> {
  return {
    list: (query: ListQuery = {}) => apiGet<PageResult<T>>(path, { ...query }),
    get: (id: string) => apiGet<T>(`${path}/${id}`),
    create: (payload: Partial<T>) => apiPost<T>(path, payload),
    update: (id: string, payload: Partial<T>) => apiPatch<T>(`${path}/${id}`, payload),
    remove: (id: string) => apiDelete(`${path}/${id}`)
  }
}

export const workflowsApi = createResource<WorkflowDto>('/workflows')
export const agentsApi = createResource<AgentDto>('/agents')
export const knowledgeBasesApi = createResource<KnowledgeBaseDto>('/knowledge-bases')
export const datasetsApi = createResource<DatasetDto>('/datasets')
export const promptsApi = createResource<PromptDto>('/prompts')
export const toolsApi = createResource<ToolDto>('/tools')
export const providersApi = createResource<ProviderDto>('/providers')
export const appsApi = createResource<AppDto>('/apps')
export const pluginsApi = createResource<PluginDto>('/plugins')
