"""测试用的假上游：一个最小的 OpenAI 兼容服务。

用途：在没有真实 API Key 的机器上，验证 `services/llm/openai_compatible.py` 的
流式解析、usage 读取与 probe 逻辑 —— 假上游走的是**真 HTTP + 真 SSE**，
只是生成内容固定，所以能证明客户端代码是对的。

启动：uvicorn tests.fake_upstream:app --port 5399
"""

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI(title="fake-openai-upstream")

REPLY = "这是一个来自假上游的真实 SSE 响应，用于验证客户端解析。"
CHUNKS = [REPLY[i : i + 6] for i in range(0, len(REPLY), 6)]


@app.get("/v1/models")
def list_models() -> dict:
    return {"object": "list", "data": [{"id": "fake-model", "object": "model"}]}


async def _events() -> AsyncIterator[bytes]:
    for index, chunk in enumerate(CHUNKS):
        payload = {
            "id": "chatcmpl-fake",
            "object": "chat.completion.chunk",
            "model": "fake-model",
            "choices": [{"index": 0, "delta": {"content": chunk}, "finish_reason": None}],
        }
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode()
        await asyncio.sleep(0.01)

    # 最后一片带 usage（OpenAI / DeepSeek 都支持 stream_options.include_usage）
    yield (
        "data: "
        + json.dumps(
            {
                "id": "chatcmpl-fake",
                "object": "chat.completion.chunk",
                "model": "fake-model",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 11, "completion_tokens": len(CHUNKS)},
            },
            ensure_ascii=False,
        )
        + "\n\n"
    ).encode()
    yield b"data: [DONE]\n\n"


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> StreamingResponse:
    body = await request.json()
    assert body.get("stream") is True, "客户端必须用流式"
    return StreamingResponse(_events(), media_type="text/event-stream")


@app.get("/health")
def health() -> dict:
    return {"ok": True}
