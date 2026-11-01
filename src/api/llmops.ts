/**
 * LLMOps 的接口。
 * 后端 /api/llmops/* 全部从 traces 表聚合出来，前端只负责画。
 */

import { apiGet, apiPost } from './http'

export type LlmopsCards = {
  totalCalls: number
  successRate: number
  avgLatencyMs: number
  totalCostUsd: number
  totalTokens: number
  activeAlerts: number
}

export type LlmopsHealth = {
  id: string
  name: string
  status: string
  modelCount: number
  enabled: boolean
}

export type AlertDto = {
  id: string
  title: string
  detail: string
  severity: string
  status: string
  source: string
  created_at: string
}

export type LlmopsOverview = {
  cards: LlmopsCards
  health: LlmopsHealth[]
  recentAlerts: AlertDto[]
}

export type CostPoint = {
  day: string
  total: number
  [model: string]: string | number
}

export type CostSeries = {
  models: string[]
  series: CostPoint[]
}

export type ModelPerf = {
  model: string
  calls: number
  successRate: number
  avgLatencyMs: number
  totalCostUsd: number
  totalTokens: number
}

export type AbTestDto = {
  id: string
  name: string
  model_a: string
  model_b: string
  status: string
  sample_size: number
  winner: string | null
  started_at: string
}

export function getOverview(): Promise<LlmopsOverview> {
  return apiGet<LlmopsOverview>('/llmops/overview')
}

export function getCostSeries(days = 15): Promise<CostSeries> {
  return apiGet<CostSeries>('/llmops/cost/series', { days })
}

export function getModelPerf(): Promise<ModelPerf[]> {
  return apiGet<ModelPerf[]>('/llmops/models')
}

export function getAbTests(): Promise<AbTestDto[]> {
  return apiGet<AbTestDto[]>('/llmops/ab-tests')
}

export function getAlerts(status?: string): Promise<AlertDto[]> {
  return apiGet<AlertDto[]>('/alerts', status ? { status } : undefined)
}

export function resolveAlert(id: string): Promise<AlertDto> {
  // 后端是 POST（GET 会 405），之前写成 apiGet 点「标记解决」会静默失败
  return apiPost<AlertDto>(`/alerts/${id}/resolve`)
}
