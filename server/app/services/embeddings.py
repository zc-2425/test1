"""Embedding 服务。

两条实现，同一个出口：

- real：OpenAI 兼容的 `POST /embeddings`（硅基流动 / OpenAI / Ollama 都通）
- mock：**本地哈希向量**（feature hashing）。不是随机数——它保证
  「词面相近的文本向量也相近」，所以离线时检索仍然有意义，测试也能断言排序。

约定：所有向量在**返回前就 L2 归一化**，检索时点积即余弦。
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

import httpx
import numpy as np

from app.core.config import get_settings


@dataclass(slots=True)
class EmbeddingConfig:
    provider: str
    base_url: str
    model: str
    dim: int
    api_key: str | None
    batch: int = 32
    timeout: float = 60.0

    @property
    def usable(self) -> bool:
        return bool(self.api_key)


def resolve_config() -> EmbeddingConfig:
    settings = get_settings()
    return EmbeddingConfig(
        provider=settings.embedding_provider,
        base_url=settings.embedding_base_url,
        model=settings.embedding_model,
        dim=settings.embedding_dim,
        api_key=settings.embedding_api_key,
        batch=settings.embedding_batch,
        timeout=settings.embedding_timeout,
    )


def use_real(config: EmbeddingConfig | None = None) -> bool:
    settings = get_settings()
    if settings.embedding_mode == "mock":
        return False
    config = config or resolve_config()
    if settings.embedding_mode == "real":
        return True
    return config.usable


def _normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        return vector.astype(np.float32)
    return (vector / norm).astype(np.float32)


def _hash_embed(texts: list[str], dim: int) -> list[np.ndarray]:
    """字符 bigram 哈希到固定维度：词面重叠越多，余弦越高。

    这是真实可用的词法检索（类似 hashing vectorizer），
    不是「假装有语义」的随机向量。
    """
    from app.services.rag import tokenize  # 避免循环导入

    out: list[np.ndarray] = []
    for text in texts:
        vector = np.zeros(dim, dtype=np.float32)
        for token in tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        out.append(_normalize(vector))
    return out


def _real_embed(texts: list[str], config: EmbeddingConfig) -> list[np.ndarray]:
    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    vectors: list[np.ndarray] = []
    with httpx.Client(timeout=config.timeout) as client:
        for start in range(0, len(texts), config.batch):
            batch = texts[start : start + config.batch]
            response = client.post(
                f"{config.base_url.rstrip('/')}/embeddings",
                headers=headers,
                json={"model": config.model, "input": batch},
            )
            if response.status_code >= 400:
                raise RuntimeError(
                    f"embedding 失败（HTTP {response.status_code}）：{response.text[:300]}"
                )
            payload = response.json()
            # 按 index 回填，防止上游乱序
            ordered = sorted(payload.get("data", []), key=lambda item: item.get("index", 0))
            for item in ordered:
                vectors.append(_normalize(np.asarray(item["embedding"], dtype=np.float32)))

    return vectors


def embed_texts(texts: list[str], config: EmbeddingConfig | None = None) -> tuple[list[np.ndarray], str]:
    """返回 (归一化向量列表, 实际使用的模式 real|mock)。"""
    config = config or resolve_config()
    if not texts:
        return [], "real" if use_real(config) else "mock"

    if use_real(config):
        return _real_embed(texts, config), "real"
    return _hash_embed(texts, config.dim), "mock"


def to_bytes(vector: np.ndarray) -> bytes:
    return vector.astype(np.float32).tobytes()


def from_bytes(raw: bytes, dim: int) -> np.ndarray:
    return np.frombuffer(raw, dtype=np.float32)[:dim]


def cosine_top_k(
    query: np.ndarray, matrix: np.ndarray, top_k: int
) -> list[tuple[int, float]]:
    """矩阵已归一化，点积即余弦。返回 [(行号, 分数)]，按分数倒序。"""
    if matrix.size == 0:
        return []
    scores = matrix @ query
    k = min(top_k, len(scores))
    # argpartition 取前 k，再对这 k 个排序，避免全量排序
    candidate = np.argpartition(-scores, k - 1)[:k]
    ranked = sorted(candidate.tolist(), key=lambda idx: float(scores[idx]), reverse=True)
    return [(int(idx), float(scores[idx])) for idx in ranked]


def health() -> dict:
    """给前端/文档用：当前到底是真 embedding 还是本地哈希。"""
    config = resolve_config()
    return {
        "provider": config.provider,
        "model": config.model,
        "dim": config.dim,
        "usable": config.usable,
        "mode": "real" if use_real(config) else "mock",
    }


__all__ = [
    "EmbeddingConfig",
    "cosine_top_k",
    "embed_texts",
    "from_bytes",
    "health",
    "resolve_config",
    "to_bytes",
    "use_real",
]
