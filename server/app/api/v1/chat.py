"""对话接口：真 SSE 流式输出。

前端只需要一个 `POST /api/chat/stream`，由后端决定走真模型还是模拟：
- 配了 Key（或 APP_LLM_MODE=real）→ 转发真模型的 SSE
- 没配 → 本地模拟，并在结束事件里明确回报 mode='mock'

SSE 事件格式（与前端 api/chat.ts 约定）：
    data: {"type":"delta","content":"..."}
    data: {"type":"result","mode":"real","usage":{...},"latencyMs":123}
    data: {"type":"error","message":"..."}
    data: [DONE]
"""

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.llm import ChatMessage, LLMError, resolve_config, should_use_real
from app.services.llm import mock as mock_llm
from app.services.llm import openai_compatible as real_llm

router = APIRouter(prefix="/chat", tags=["对话"])


class ChatIn(BaseModel):
    prompt: str = ""
    input: str = ""
    model: str | None = None
    provider: str | None = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=32000)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _generate(payload: ChatIn) -> AsyncIterator[str]:
    use_real = should_use_real(payload.provider)
    config = resolve_config(payload.provider, payload.model)

    if config is None:
        yield _sse({"type": "error", "message": f"不支持的提供商：{payload.provider}"})
        yield "data: [DONE]\n\n"
        return

    messages = []
    if payload.prompt.strip():
        messages.append(ChatMessage(role="system", content=payload.prompt.strip()))
    messages.append(ChatMessage(role="user", content=payload.input.strip() or "你好"))

    impl = real_llm if use_real else mock_llm
    try:
        async for chunk in impl.stream_chat(
            config,
            messages,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        ):
            if isinstance(chunk, str):
                yield _sse({"type": "delta", "content": chunk})
            else:
                yield _sse(
                    {
                        "type": "result",
                        "mode": chunk.mode,
                        "provider": chunk.provider,
                        "model": chunk.model,
                        "usage": {
                            "promptTokens": chunk.prompt_tokens,
                            "completionTokens": chunk.completion_tokens,
                        },
                        "latencyMs": chunk.latency_ms,
                        "finishReason": chunk.finish_reason,
                    }
                )
    except LLMError as exc:
        yield _sse({"type": "error", "message": str(exc)})
    except Exception as exc:  # noqa: BLE001 - 流里出错必须转成事件，不能抛穿连接
        yield _sse({"type": "error", "message": f"调用失败：{exc}"})

    yield "data: [DONE]\n\n"


@router.post("/stream")
async def chat_stream(payload: ChatIn) -> StreamingResponse:
    return StreamingResponse(
        _generate(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # 关掉 nginx 的缓冲，否则流式会被攒成一坨
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/status")
def chat_status() -> dict:
    """前端用它在界面上标注「真实 / 模拟」。"""
    from app.core.config import get_settings

    settings = get_settings()
    config = resolve_config(settings.llm_default_provider)
    return {
        "mode": settings.llm_mode,
        "useReal": should_use_real(settings.llm_default_provider),
        "provider": settings.llm_default_provider,
        "model": config.model if config else None,
        "hasKey": bool(config and config.api_key),
    }
