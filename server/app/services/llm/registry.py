"""厂商注册表：把「厂商 slug」解析成一次调用需要的配置。

Key 一律从环境变量 / server/.env 读，绝不从数据库读 ——
库里只存掩码用于展示，真 Key 落库等于把密钥写进备份文件。
"""

from app.core.config import get_settings
from app.services.llm.base import LLMConfig

# provider slug → (base_url 设置字段, api_key 设置字段, 默认模型, 是否需要 Key)
_SPECS: dict[str, tuple[str, str | None, str, bool]] = {
    "deepseek": ("deepseek_base_url", "deepseek_api_key", "deepseek-chat", True),
    "openai": ("openai_base_url", "openai_api_key", "gpt-4o-mini", True),
    # 硅基流动：一个 Key 同时提供 chat 与 embedding，练手最省事
    "siliconflow": ("siliconflow_base_url", "siliconflow_api_key", "deepseek-ai/DeepSeek-V3.2", True),
    # 本地 Ollama 跑 OpenAI 兼容层，不需要 Key
    "ollama": ("ollama_base_url", None, "llama3.1", False),
}

# 数据库里的 slug 与上面的 key 可能不完全一致，这里做一次归一
_ALIASES = {
    "openai": "openai",
    "deepseek": "deepseek",
    "siliconflow": "siliconflow",
    "ollama": "ollama",
    "azure-openai": "openai",
    "aws-bedrock": "openai",
}


def supported_providers() -> list[str]:
    """能走真调用的厂商（其它厂商在 UI 上会提示不支持真实测试）。"""
    return sorted(_SPECS)


def resolve_provider_slug(slug: str | None) -> str | None:
    if not slug:
        return None
    key = slug.strip().lower()
    return _ALIASES.get(key)


def resolve_config(provider: str | None = None, model: str | None = None) -> LLMConfig | None:
    """返回该厂商的配置；厂商不支持时返回 None。"""
    settings = get_settings()
    slug = resolve_provider_slug(provider) or settings.llm_default_provider
    spec = _SPECS.get(slug)
    if spec is None:
        return None

    base_field, key_field, default_model, needs_key = spec
    api_key = getattr(settings, key_field) if key_field else None
    # 硅基流动一个 Key 通吃：没单独配 LLM Key 时复用 embedding 的
    if slug == "siliconflow" and not api_key:
        api_key = settings.embedding_api_key
    if needs_key and not api_key:
        api_key = None

    preferred = (
        settings.llm_default_model if slug == settings.llm_default_provider else default_model
    )
    chosen_model = model or preferred
    # 硅基流动的模型 id 一定带厂商前缀（如 deepseek-ai/DeepSeek-V4-Flash）。
    # 库里存的旧配置可能是 gpt-4o 这类裸名，直接送去会 400（code 20012），
    # 所以回落到「本厂商的默认模型」，实际用了什么会在 result 事件里回报。
    if slug == "siliconflow" and chosen_model and "/" not in chosen_model:
        chosen_model = preferred

    return LLMConfig(
        provider=slug,
        base_url=getattr(settings, base_field),
        model=chosen_model,
        api_key=api_key,
        timeout=settings.llm_timeout,
    )


def should_use_real(provider: str | None = None) -> bool:
    """真正的开关：mode=auto 时看有没有 Key，mode=real 强制真，mode=mock 强制假。"""
    settings = get_settings()
    if settings.llm_mode == "mock":
        return False

    config = resolve_config(provider)
    if config is None:
        return False
    if settings.llm_mode == "real":
        return True
    return config.ready

def env_var_for(provider: str | None) -> str | None:
    """给前端提示「该把 Key 写进哪个环境变量」。"""
    slug = resolve_provider_slug(provider)
    spec = _SPECS.get(slug) if slug else None
    if spec is None or spec[1] is None:
        return None
    return f"APP_{spec[1].upper()}"
