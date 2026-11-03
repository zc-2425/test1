/**
 * 对话/生成的流式接口 —— 真 SSE。
 *
 * 走 `POST /api/chat/stream`，后端决定用真模型还是模拟：
 * - 配了 Key（或 APP_LLM_MODE=real）→ 转发上游 SSE
 * - 没配 → 本地模拟，并在 result 事件里回报 mode='mock'
 *
 * 所以前端**不需要知道**当前是真还是假，只看 result.mode 决定要不要显示「模拟输出」角标。
 * 这正是 P12 想要的可插拔：换模型、换厂商都不用动前端。
 */

const BASE = import.meta.env.VITE_API_BASE ?? '/api'

export type ChatMode = 'real' | 'mock'

export interface ChatRequest {
  prompt: string
  input: string
  model?: string
  provider?: string
  temperature?: number
  maxTokens?: number
  /** 会话归属：写进 conversations / traces */
  promptId?: string
  agentId?: string
  appId?: string
  conversationId?: string
  /** 关掉就不落库 */
  persist?: boolean
  /** 绑定知识库：后端先检索再生成 */
  kbId?: string
  ragTopK?: number
}

export interface ChatUsage {
  mode: ChatMode
  provider: string
  model: string
  promptTokens: number
  completionTokens: number
  latencyMs: number
  finishReason: string
  /** 本次调用所属会话，便于跳转查看历史 */
  conversationId: string | null
  /** 检索阶段耗时（未绑定知识库时为 0） */
  ragMs: number
  /** 命中的知识库片段 */
  citations: Citation[]
}

export type Citation = {
  chunkId: string
  docId: string
  docName: string
  position: number
  score: number
  preview: string
}

export interface ChatStatus {
  mode: 'auto' | 'real' | 'mock'
  useReal: boolean
  provider: string
  model: string | null
  hasKey: boolean
}

export interface StreamOptions {
  signal?: AbortSignal
}

/** 当前后端的调用方式，用于在界面上标注「真实 / 模拟」 */
export async function fetchChatStatus(): Promise<ChatStatus> {
  const response = await fetch(`${BASE}/chat/status`, { headers: { Accept: 'application/json' } })
  if (!response.ok) throw new Error(`状态查询失败：HTTP ${response.status}`)
  return (await response.json()) as ChatStatus
}

export async function streamChat(
  request: ChatRequest,
  onDelta: (delta: string) => void,
  options: StreamOptions = {}
): Promise<ChatUsage> {
  const response = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({
      prompt: request.prompt,
      input: request.input,
      model: request.model,
      provider: request.provider,
      temperature: request.temperature ?? 0.7,
      max_tokens: request.maxTokens,
      prompt_id: request.promptId,
      agent_id: request.agentId,
      app_id: request.appId,
      conversation_id: request.conversationId,
      persist: request.persist ?? true,
      kb_id: request.kbId,
      rag_top_k: request.ragTopK
    }),
    signal: options.signal
  })

  if (!response.ok || !response.body) {
    const detail = await response.text().catch(() => '')
    throw new Error(`请求失败（HTTP ${response.status}）${detail ? `：${detail.slice(0, 200)}` : ''}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let usage: ChatUsage | null = null
  let failure: string | null = null

  // SSE 以空行分隔事件；chunk 边界可能把一个事件切成两半，所以按 buffer 累积再切
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() ?? ''

    for (const block of blocks) {
      const dataLine = block
        .split('\n')
        .map((line) => line.trim())
        .find((line) => line.startsWith('data:'))
      if (!dataLine) continue

      const payload = dataLine.slice(5).trim()
      if (!payload || payload === '[DONE]') continue

      let event: Record<string, unknown>
      try {
        event = JSON.parse(payload) as Record<string, unknown>
      } catch {
        continue
      }

      if (event.type === 'delta') {
        onDelta(String(event.content ?? ''))
      } else if (event.type === 'result') {
        const token = (event.usage ?? {}) as { promptTokens?: number; completionTokens?: number }
        usage = {
          mode: (event.mode as ChatMode) ?? 'mock',
          provider: String(event.provider ?? ''),
          model: String(event.model ?? ''),
          promptTokens: Number(token.promptTokens ?? 0),
          completionTokens: Number(token.completionTokens ?? 0),
          latencyMs: Number(event.latencyMs ?? 0),
          finishReason: String(event.finishReason ?? 'stop'),
          conversationId: event.conversationId ? String(event.conversationId) : null,
          ragMs: Number(event.ragMs ?? 0),
          citations: Array.isArray(event.citations) ? (event.citations as Citation[]) : []
        }
      } else if (event.type === 'error') {
        failure = String(event.message ?? '未知错误')
      }
    }
  }

  if (failure) throw new Error(failure)
  if (!usage) throw new Error('连接中断：没有收到结束事件')
  return usage
}
