/**
 * 评测接口：用例 CRUD + 跑一次评测 + 历史对比。
 * 判分是「期望要点命中率」，纯确定性，改完提示词可以直接看分数变化。
 */

import { apiDelete, apiGet, apiPatch, apiPost } from './http'

export type EvalCaseDto = {
  id: string
  prompt_id: string | null
  kb_id: string | null
  question: string
  expected: string
  enabled: boolean
  created_at: string
}

export type EvalResultDto = {
  id: string
  run_id: string
  case_id: string
  question: string
  answer: string
  matched: number
  total_points: number
  score: number
  passed: boolean
  missing: string
  latency_ms: number
  citations: string | null
  created_at: string
}

export type EvalRunDto = {
  id: string
  prompt_id: string | null
  kb_id: string | null
  model: string
  mode: string
  total: number
  passed: number
  avg_score: number
  threshold: number
  took_ms: number
  note: string
  created_at: string
}

export type EvalRunDetail = { run: EvalRunDto; results: EvalResultDto[] }

export type CaseInput = {
  question: string
  expected: string
  prompt_id?: string | null
  kb_id?: string | null
  enabled?: boolean
}

export type RunInput = {
  prompt_id?: string | null
  prompt?: string
  kb_id?: string | null
  threshold?: number
  top_k?: number
  note?: string
}

export function listCases(promptId: string): Promise<EvalCaseDto[]> {
  return apiGet<EvalCaseDto[]>('/eval/cases', { prompt_id: promptId })
}

export function createCase(input: CaseInput): Promise<EvalCaseDto> {
  return apiPost<EvalCaseDto>('/eval/cases', input)
}

export function updateCase(
  id: string,
  patch: Partial<Pick<EvalCaseDto, 'question' | 'expected' | 'enabled' | 'kb_id'>>
): Promise<EvalCaseDto> {
  return apiPatch<EvalCaseDto>(`/eval/cases/${id}`, patch)
}

export function deleteCase(id: string): Promise<void> {
  return apiDelete(`/eval/cases/${id}`)
}

/** 同步跑完才返回：用例多时请求会比较久 */
export function runEval(input: RunInput): Promise<EvalRunDetail> {
  return apiPost<EvalRunDetail>('/eval/runs', input)
}

export function listRuns(promptId: string): Promise<EvalRunDto[]> {
  return apiGet<EvalRunDto[]>('/eval/runs', { prompt_id: promptId })
}

export function getRun(runId: string): Promise<EvalRunDetail> {
  return apiGet<EvalRunDetail>(`/eval/runs/${runId}`)
}
