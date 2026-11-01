"""模拟实现：没有 Key 时的回落路径。

保留它不是为了「假装成功」，而是为了在没配 Key 的机器上也能把前端交互跑通；
结果事件里会明确回报 mode='mock'，前端据此显示「模拟输出」角标。
"""

import asyncio
import time
from collections.abc import AsyncIterator

from app.services.llm.base import ChatMessage, LLMConfig, LLMResult
from app.services.llm.openai_compatible import _estimate_tokens


def _compose(messages: list[ChatMessage]) -> str:
    question = ""
    for message in reversed(messages):
        if message.role == "user":
            question = message.content.strip()
            break
    question = question or "（空输入）"
    return "\n".join(
        [
            f"收到问题：{question}",
            "",
            "这是本地模拟输出（未配置模型 API Key）。",
            "把 Key 写进 server/.env 的 APP_DEEPSEEK_API_KEY 后，同一个界面会显示真实生成内容。",
            "",
            "模拟回答要点：",
            "1. 先确认需求边界；",
            "2. 结合知识库给出可溯源结论；",
            "3. 信息不足时明确说明缺什么。",
        ]
    )


async def stream_chat(
    config: LLMConfig,
    messages: list[ChatMessage],
    *,
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> AsyncIterator[str | LLMResult]:
    del temperature, max_tokens  # 模拟实现不需要
    reply = _compose(messages)
    started = time.perf_counter()

    for index in range(0, len(reply), 3):
        yield reply[index : index + 3]
        await asyncio.sleep(0.012)

    yield LLMResult(
        mode="mock",
        provider=config.provider,
        model=config.model,
        prompt_tokens=sum(_estimate_tokens(m.content) for m in messages),
        completion_tokens=_estimate_tokens(reply),
        latency_ms=int((time.perf_counter() - started) * 1000),
    )


async def probe(config: LLMConfig) -> tuple[bool, int, str]:
    del config
    return False, 0, "未配置 API Key，无法真实连通性测试"
