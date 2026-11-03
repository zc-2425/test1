/**
 * 会话与调用记录。
 * P1 起这些数据由真实交互产生（对话、提示词测试、工作流运行），不再是种子。
 */

import type { PageResult } from '@/types/common'
import { apiDelete, apiGet } from './http'

export type ConversationDto = {
  id: string
  title: string
  /** prompt_test | workflow_run | app_chat | agent_chat */
  source: string
  prompt_id: string | null
  agent_id: string | null
  app_id: string | null
  workflow_id: string | null
  message_count: number
  total_tokens: number
  total_cost_usd: number
  created_at: string
  updated_at: string
}

export type MessageDto = {
  id: string
  conversation_id: string
  role: string
  content: string
  tokens: number
  latency_ms: number
  mode: string
  /** 引用来源（JSON 文本，可能为 null） */
  citations: string | null
  created_at: string
}

export type TraceDto = {
  id: string
  provider: string
  model: string
  prompt_tokens: number
  completion_tokens: number
  cost_usd: number
  latency_ms: number
  status: string
  kind: string
  mode: string
  error: string | null
  conversation_id: string | null
  day: string
  created_at: string
}

export type ConversationDetail = {
  conversation: ConversationDto
  messages: MessageDto[]
  traces: TraceDto[]
}

export type ConversationQuery = {
  page?: number
  size?: number
  source?: string
  prompt_id?: string
  agent_id?: string
  app_id?: string
  workflow_id?: string
}

export function listConversations(query: ConversationQuery = {}): Promise<PageResult<ConversationDto>> {
  return apiGet<PageResult<ConversationDto>>('/conversations', { ...query })
}

export function getConversation(id: string): Promise<ConversationDetail> {
  return apiGet<ConversationDetail>(`/conversations/${id}`)
}

export function deleteConversation(id: string): Promise<void> {
  return apiDelete(`/conversations/${id}`)
}

export function listTraces(
  query: { kind?: string; mode?: string; status?: string; page?: number; size?: number } = {}
): Promise<PageResult<TraceDto>> {
  return apiGet<PageResult<TraceDto>>('/traces', { ...query })
}
