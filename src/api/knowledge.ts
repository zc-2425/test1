/**
 * 知识库专属接口（通用 CRUD 在 resources.ts）。
 * 「重建索引」与「文档列表」是知识库独有的两个端点。
 */

import { apiGet, apiPost } from './http'
import type { KnowledgeBaseDto } from './types'

export type KbDocumentDto = {
  id: string
  name: string
  size: string
  chunks: number
  status: string
}

/** 文档列表（原型没有这个页面，按 doc_count 生成占位文档） */
export function listDocuments(kbId: string): Promise<KbDocumentDto[]> {
  return apiGet<KbDocumentDto[]>(`/knowledge-bases/${kbId}/documents`)
}

/** 重建索引：后端用后台任务把 vector_progress 从 5% 推到 100% */
export function reindexKnowledgeBase(kbId: string): Promise<KnowledgeBaseDto> {
  return apiPost<KnowledgeBaseDto>(`/knowledge-bases/${kbId}/reindex`)
}
