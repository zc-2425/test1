"""OpenAI 兼容协议的流式客户端。

DeepSeek、OpenAI、Ollama、vLLM、DashScope 兼容模式都实现同一套
`POST {base_url}/chat/completions` + SSE，所以一个客户端够用。

刻意不引 openai SDK：这里只需要一个流式 POST，httpx 足够，
少一层依赖也少一个版本兼容问题。
"""

import json
import time
from collections.abc import AsyncIterator

import httpx

from app.services.llm.base import ChatMessage, LLMConfig, LLMError, LLMResult


def _headers(config: LLMConfig) -> dict[str, str]:
    headers = {"Content-Type": "application/json", **config.extra_headers}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    return headers


def _estimate_tokens(text: str) -> int:
    """粗略估算：中文 1.5 字/token，其余 4 字符/token。真实用量优先取上游 usage。"""
    chinese = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fa5")
    rest = len(text) - chinese
    return max(1, round(chinese / 1.5 + rest / 4))


async def stream_chat(
    config: LLMConfig,
    messages: list[ChatMessage],
    *,
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> AsyncIterator[str | LLMResult]:
    """逐片产出文本，最后产出一个 LLMResult（用 isinstance 区分）。"""
    payload: dict[str, object] = {
        "model": config.model,
        "messages": [message.as_payload() for message in messages],
        "stream": True,
        "temperature": temperature,
        # 让上游在最后一片带上 usage（OpenAI/DeepSeek 都支持）
        "stream_options": {"include_usage": True},
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    started = time.perf_counter()
    chunks: list[str] = []
    usage: dict[str, int] | None = None
    finish_reason = "stop"

    async with httpx.AsyncClient(timeout=config.timeout) as client:
        try:
            async with client.stream(
                "POST",
                f"{config.base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=_headers(config),
            ) as response:
                if response.status_code >= 400:
                    detail = (await response.aread()).decode("utf-8", "replace")[:400]
                    raise LLMError(
                        f"{config.provider} 返回 {response.status_code}：{detail}",
                        status_code=response.status_code,
                    )

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    if isinstance(event.get("usage"), dict):
                        usage = {
                            "prompt": int(event["usage"].get("prompt_tokens") or 0),
                            "completion": int(event["usage"].get("completion_tokens") or 0),
                        }

                    for choice in event.get("choices") or []:
                        delta = (choice.get("delta") or {}).get("content")
                        if delta:
                            chunks.append(delta)
                            yield delta
                        if choice.get("finish_reason"):
                            finish_reason = str(choice["finish_reason"])
        except httpx.HTTPError as exc:
            raise LLMError(f"连接 {config.provider} 失败：{exc}") from exc

    text = "".join(chunks)
    yield LLMResult(
        mode="real",
        provider=config.provider,
        model=config.model,
        prompt_tokens=usage["prompt"] if usage else sum(_estimate_tokens(m.content) for m in messages),
        completion_tokens=usage["completion"] if usage else _estimate_tokens(text),
        latency_ms=int((time.perf_counter() - started) * 1000),
        finish_reason=finish_reason,
    )


async def probe(config: LLMConfig) -> tuple[bool, int, str]:
    """连通性测试：拉一次 /models，比跑一次对话便宜得多。

    返回 (是否成功, 延迟毫秒, 错误信息或空串)。
    """
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{config.base_url.rstrip('/')}/models", headers=_headers(config)
            )
        latency = int((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            body = response.text[:300]
            return False, latency, f"HTTP {response.status_code}：{body}"
        try:
            count = len((response.json() or {}).get("data") or [])
        except ValueError:
            count = 0
        return True, latency, f"{count} 个模型可用" if count else ""
    except httpx.HTTPError as exc:
        return False, int((time.perf_counter() - started) * 1000), f"连接失败：{exc}"
