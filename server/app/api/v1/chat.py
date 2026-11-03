"""对话接口：真 SSE 流式输出 + 会话落库 + trace 埋点。

前端只需要一个 `POST /api/chat/stream`，由后端决定走真模型还是模拟：
- 配了 Key（或 APP_LLM_MODE=real）→ 转发真模型的 SSE
- 没配 → 本地模拟，并在结束事件里明确回报 mode='mock'

P1 起，每次调用都会：
1. 建（或复用）一条 conversation
2. 把 user / assistant 两条 message 落库
3. 写一条 trace（token、耗时、成本、模式、错误），LLMOps 的所有聚合都读它

SSE 事件格式（与前端 api/chat.ts 约定）：
    data: {"type":"delta","content":"..."}
    data: {"type":"result","mode":"real","conversationId":"conv-xxx","usage":{...}}
    data: {"type":"error","message":"..."}
    data: [DONE]
"""

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlmodel import Session

from app import models
from app.db import engine
from app.services import telemetry
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

    # 会话归属：谁在什么场景下发的这次请求
    conversation_id: str | None = None
    prompt_id: str | None = None
    agent_id: str | None = None
    app_id: str | None = None
    # 关掉就不落库（连通性试验之类）
    persist: bool = True


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _source_of(payload: ChatIn) -> str:
    if payload.app_id:
        return "app_chat"
    if payload.agent_id:
        return "agent_chat"
    return "prompt_test"


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

    # 流式响应期间请求作用域的 session 已经结束，这里单独开一个
    with Session(engine) as session:
        conversation: models.Conversation | None = None
        if payload.persist:
            if payload.conversation_id:
                conversation = session.get(models.Conversation, payload.conversation_id)
            if conversation is None:
                conversation = telemetry.start_conversation(
                    session,
                    source=_source_of(payload),
                    title=payload.input.strip()[:60],
                    prompt_id=payload.prompt_id,
                    agent_id=payload.agent_id,
                    app_id=payload.app_id,
                )
            if payload.input.strip():
                telemetry.append_message(
                    session, conversation, role="user", content=payload.input.strip()
                )

        speaker = ""
        result = None
        failure: str | None = None

        try:
            async for chunk in impl.stream_chat(
                config,
                messages,
                temperature=payload.temperature,
                max_tokens=payload.max_tokens,
            ):
                if isinstance(chunk, str):
                    speaker += chunk
                    yield _sse({"type": "delta", "content": chunk})
                else:
                    result = chunk
        except LLMError as exc:
            failure = str(exc)
            yield _sse({"type": "error", "message": failure})
        except Exception as exc:  # noqa: BLE001 - 流里出错必须转成事件
            failure = f"调用失败：{exc}"
            yield _sse({"type": "error", "message": failure})

        if payload.persist and conversation is not None:
            mode = result.mode if result else ("real" if use_real else "mock")
            prompt_tokens = result.prompt_tokens if result else 0
            completion_tokens = result.completion_tokens if result else 0
            latency = result.latency_ms if result else 0

            if speaker.strip():
                telemetry.append_message(
                    session,
                    conversation,
                    role="assistant",
                    content=speaker,
                    tokens=completion_tokens,
                    latency_ms=latency,
                    mode=mode,
                )
            telemetry.record_trace(
                session,
                kind=_source_of(payload),
                provider=config.provider,
                model=config.model,
                mode=mode,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency,
                status="失败" if failure else "成功",
                error=failure,
                conversation_id=conversation.id,
                agent_id=payload.agent_id,
                app_id=payload.app_id,
            )

        if result is not None:
            yield _sse(
                {
                    "type": "result",
                    "mode": result.mode,
                    "provider": result.provider,
                    "model": result.model,
                    "conversationId": conversation.id if conversation else None,
                    "usage": {
                        "promptTokens": result.prompt_tokens,
                        "completionTokens": result.completion_tokens,
                    },
                    "latencyMs": result.latency_ms,
                    "finishReason": result.finish_reason,
                }
            )

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
