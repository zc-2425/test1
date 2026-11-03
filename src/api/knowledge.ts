/**
 * 知识库专属接口（通用 CRUD 在 resources.ts）。
 * P2 起文档、分块、向量、检索都是真的：上传走 multipart，检索走后端余弦。
 */

import { apiDelete, apiGet, apiPost } from './http'
import type { KnowledgeBaseDto } from './types'

export type KbDocumentDto = {
  id: string
  name: string
  fileType: string
  size: string
  sizeBytes: number
  charCount: number
  chunks: number
  status: string
  error: string | null
  createdAt: string
}

export type KbChunkDto = {
  id: string
  position: number
  chars: number
  content: string
}

export type KbChunkPage = {
  docId: string
  docName: string
  total: number
  chunks: KbChunkDto[]
}

export type KbSearchHit = {
  chunkId: string
  docId: string
  docName: string
  position: number
  score: number
  preview: string
}

export type KbSearchResult = {
  query: string
  mode: string
  model?: string
  tookMs: number
  scanned: number
  hits: KbSearchHit[]
}

export type EmbeddingStatus = {
  provider: string
  model: string
  dim: number
  usable: boolean
  mode: string
}

export type UploadResult = {
  id: string
  name: string
  chunks: number
  status: string
  mode: string
  model: string
  tookMs: number
}

export function listDocuments(kbId: string): Promise<KbDocumentDto[]> {
  return apiGet<KbDocumentDto[]>(`/knowledge-bases/${kbId}/documents`)
}

/** 上传并立即索引入库（切块 + embedding + 存向量） */
export async function uploadDocument(kbId: string, file: File): Promise<UploadResult> {
  const form = new FormData()
  form.append('file', file)
  const response = await fetch(`/api/knowledge-bases/${kbId}/documents`, {
    method: 'POST',
    body: form
  })
  if (!response.ok) {
    const detail = await response.text().catch(() => '')
    let message = `上传失败（HTTP ${response.status}）`
    try {
      const parsed = JSON.parse(detail) as { detail?: string }
      if (parsed.detail) message = parsed.detail
    } catch {
      if (detail) message = `${message}：${detail.slice(0, 160)}`
    }
    throw new Error(message)
  }
  return (await response.json()) as UploadResult
}

export function deleteDocument(kbId: string, docId: string): Promise<void> {
  return apiDelete(`/knowledge-bases/${kbId}/documents/${docId}`)
}

export function listChunks(kbId: string, docId: string, limit = 50): Promise<KbChunkPage> {
  return apiGet<KbChunkPage>(`/knowledge-bases/${kbId}/documents/${docId}/chunks`, { limit })
}

/** 检索测试：真向量检索，返回分数与来源 */
export function searchKnowledgeBase(
  kbId: string,
  query: string,
  topK = 5
): Promise<KbSearchResult> {
  return apiPost<KbSearchResult>(`/knowledge-bases/${kbId}/search`, {
    query,
    top_k: topK
  })
}

export function embeddingStatus(): Promise<EmbeddingStatus> {
  return apiGet<EmbeddingStatus>('/knowledge-bases/embeddings/status')
}

/** 重建索引：后台按文档逐个重切块并重新向量化 */
export function reindexKnowledgeBase(kbId: string): Promise<KnowledgeBaseDto> {
  return apiPost<KnowledgeBaseDto>(`/knowledge-bases/${kbId}/reindex`)
}
