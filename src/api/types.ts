/**
 * 后端 DTO（字段与 SQLModel 表一致，snake_case）。
 * 放在这里集中定义，页面与 api 层共用同一份类型；
 * 将来若改成 camelCase，只需在 api 层加一层映射，页面不用动。
 */

export type ListQuery = {
  page?: number
  size?: number
  q?: string
  status?: string
  type?: string
  sort?: string
  order?: 'asc' | 'desc'
}

export type WorkflowDto = {
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

export type AgentDto = {
  id: string
  name: string
  description: string
  type: string
  strategy: string
  status: string
  avatar: string | null
  system_prompt: string
  model_id: string | null
  tool_count: number
  run_count: number
  last_run_at: string | null
  created_at: string
  updated_at: string
}

export type KnowledgeBaseDto = {
  id: string
  name: string
  description: string
  doc_count: number
  size_label: string
  embedding_model: string
  chunk_size: number
  chunk_overlap: number
  status: string
  vector_progress: number
  created_at: string
  updated_at: string
}

export type DatasetDto = {
  id: string
  name: string
  description: string
  type: string
  record_count: number
  size_label: string
  parse_status: string
  progress: number
  created_at: string | null
  updated_at: string
}

export type PromptDto = {
  id: string
  name: string
  description: string
  category: string
  model_id: string | null
  version: string
  status: string
  usage_count: number
  content: string
  created_at: string
  updated_at: string
}

export type ToolDto = {
  id: string
  name: string
  description: string
  type: string
  input_params: string
  input_schema: string
  status: string
  call_count: number
  created_at: string
  updated_at: string
}

export type ProviderDto = {
  id: string
  name: string
  slug: string
  model_count: number
  status: string
  api_key_masked: string
  enabled: boolean
  base_url: string | null
  created_at: string
  updated_at: string
}

export type AppDto = {
  id: string
  name: string
  description: string
  type: string
  status: string
  usage_count: number
  agent_id: string | null
  workflow_id: string | null
  created_at: string
  updated_at: string
}

export type PluginDto = {
  id: string
  name: string
  description: string
  category: string
  author: string
  rating: number
  download_count: number
  price: string
  verified: boolean
  installed: boolean
  hot: boolean
}
