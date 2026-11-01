"""LLM 层的数据结构与错误类型。"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str

    def as_payload(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(slots=True)
class LLMConfig:
    """一次调用的完整配置。api_key 为空表示走不通真调用。"""

    provider: str
    base_url: str
    model: str
    api_key: str | None = None
    timeout: float = 60.0
    extra_headers: dict[str, str] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        """ollama 这类本地服务不需要 Key，所以只判断 base_url 是否有值。"""
        return bool(self.base_url) and (bool(self.api_key) or self.provider == "ollama")


@dataclass(slots=True)
class LLMResult:
    mode: str  # 'real' | 'mock'
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    finish_reason: str = "stop"


class LLMError(RuntimeError):
    """上游返回错误或网络异常。message 会原样透给前端。"""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
