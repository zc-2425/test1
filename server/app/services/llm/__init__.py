"""LLM 服务层。

设计目标：**同一套接口，两种实现**。

- real：OpenAI 兼容协议的 SSE 客户端（DeepSeek / OpenAI / Ollama / vLLM / 通义兼容模式都走这套）
- mock：本地按字符分片的模拟输出

选哪一种由 `APP_LLM_MODE` 决定，默认 `auto`：
auto 下如果配置了对应厂商的 API Key 就走真调用，否则回落 mock —— 并在结果事件里
明确回报 `mode`，让前端能显示「模拟输出（未配置 Key）」，而不是假装成真的。
"""

from app.services.llm.base import ChatMessage, LLMConfig, LLMError, LLMResult
from app.services.llm.registry import (
    env_var_for,
    resolve_config,
    resolve_provider_slug,
    should_use_real,
    supported_providers,
)

__all__ = [
    "ChatMessage",
    "LLMConfig",
    "LLMError",
    "LLMResult",
    "env_var_for",
    "resolve_config",
    "resolve_provider_slug",
    "should_use_real",
    "supported_providers",
]
