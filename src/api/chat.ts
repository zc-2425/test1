/**
 * 对话/生成的流式接口。
 *
 * 现在这里是**本地模拟**：按字符分片吐出来，带一点抖动，用来把「流式输出」的前端结构
 * 先跑通。P12 换成真调用时，只需要把 `streamChat` 的实现替换成
 * `fetch('/api/chat/stream') + ReadableStream` 读 SSE，函数签名与回调方式都保持不变，
 * 调用方（提示词编辑器、工作流运行面板）一行都不用改。
 */

export interface ChatRequest {
  prompt: string
  input: string
  model?: string
  temperature?: number
}

export interface ChatUsage {
  promptTokens: number
  completionTokens: number
  latencyMs: number
}

export interface StreamOptions {
  /** 用于中途取消（组件卸载或用户点停止） */
  signal?: AbortSignal
  /** 每片之间的延迟，毫秒 */
  delayMs?: number
}

/** 粗略的 token 估算：中文按 1.5 字/token，英文按 4 字符/token */
export function estimateTokens(text: string): number {
  const chinese = (text.match(/[\u4e00-\u9fa5]/g) ?? []).length
  const rest = text.length - chinese
  return Math.max(1, Math.round(chinese / 1.5 + rest / 4))
}

function buildReply(request: ChatRequest): string {
  const question = request.input.trim() || '（空输入）'
  return [
    `收到问题：${question}`,
    '',
    '根据当前提示词与模型配置，我的回答分三点：',
    '1. 先确认需求边界，避免答非所问；',
    '2. 结合知识库召回的分块给出可溯源结论；',
    '3. 如果信息不足，明确说明缺少什么，而不是编造。',
    '',
    '提示：这是本地模拟的流式输出。P12 接入真实模型后，同样的界面会显示真实生成内容。'
  ].join('\n')
}

export async function streamChat(
  request: ChatRequest,
  onDelta: (delta: string) => void,
  options: StreamOptions = {}
): Promise<ChatUsage> {
  const { signal, delayMs = 28 } = options
  const reply = buildReply(request)
  const startedAt = performance.now()
  const chunkSize = 3

  for (let index = 0; index < reply.length; index += chunkSize) {
    if (signal?.aborted) break
    onDelta(reply.slice(index, index + chunkSize))
    // 模拟网络抖动，让流式看起来不像瞬发
    await new Promise((resolve) => window.setTimeout(resolve, delayMs + Math.random() * 20))
  }

  const latencyMs = Math.round(performance.now() - startedAt)
  return {
    promptTokens: estimateTokens(request.prompt) + estimateTokens(request.input),
    completionTokens: estimateTokens(reply),
    latencyMs
  }
}
