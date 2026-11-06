"""评测：把「答得好不好」变成可复现的数字。

判分方式刻意**不用 LLM 打分**：模型当裁判既贵又不稳定，同一份回答两次能给出不同分数。
这里用「期望要点命中率」—— 每个用例配几条期望内容，回答里命中几条就算几分。
好处是纯确定性、可离线、改完提示词能直接对比两次运行。

局限也写清楚：要点是字面匹配，同义表述可能漏判。所以要点要写得**贴近期望措辞**，
或者多写几条覆盖不同说法。
"""

from __future__ import annotations

import json
import re
import time
from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Session, select

from app import models
from app.services import rag
from app.services.llm import ChatMessage, LLMError, resolve_config, should_use_real
from app.services.llm import mock as mock_llm
from app.services.llm import openai_compatible as real_llm

# 要点分隔：换行、分号、竖线、顿号都算
_POINT_SPLIT = re.compile(r"[\n;；|、]+")


def split_points(expected: str) -> list[str]:
    return [item.strip() for item in _POINT_SPLIT.split(expected) if item.strip()]


def normalize(text: str) -> str:
    """去掉空白与常见标点，降低「格式不同就判错」的误伤。"""
    text = text.lower()
    text = re.sub(r"[\s\u3000]+", "", text)
    text = re.sub(r"[，。！？；：、（）()\[\]【】\"'“”‘’、,.;:!?\-—…]+", "", text)
    return text


def score_answer(answer: str, points: list[str]) -> tuple[list[str], list[str]]:
    """返回 (命中的要点, 没命中的要点)。"""
    haystack = normalize(answer)
    matched: list[str] = []
    missing: list[str] = []
    for point in points:
        needle = normalize(point)
        if needle and needle in haystack:
            matched.append(point)
        else:
            missing.append(point)
    return matched, missing


def _sse_answer(
    session: Session,
    *,
    prompt: str,
    question: str,
    kb_id: str | None,
    top_k: int,
    temperature: float,
    max_tokens: int = 400,
) -> tuple[str, list[dict], str, str]:
    """跑一次问答（非流式），返回 (回答, 引用, mode, model)。

    和 /api/chat/stream 共用同一套 RAG + LLM 逻辑，但不需要增量输出，
    所以这里同步收集完毕再返回，便于逐条判分。
    """
    import asyncio

    use_real = should_use_real()
    config = resolve_config()
    if config is None:
        raise LLMError("没有可用的模型配置")

    messages: list[ChatMessage] = []
    if prompt.strip():
        messages.append(ChatMessage(role="system", content=prompt.strip()))

    citations: list[dict] = []
    if kb_id:
        kb = session.get(models.KnowledgeBase, kb_id)
        if kb is not None:
            found = rag.search(session, kb, question, top_k)
            citations = found["hits"]
            if citations:
                blocks = [
                    f"[{index + 1}] 来源：{hit['docName']} 第 {hit['position'] + 1} 段\n{hit['content']}"
                    for index, hit in enumerate(citations)
                ]
                messages.insert(
                    0,
                    ChatMessage(
                        role="system",
                        content=(
                            "你可以参考下面的知识库片段回答问题。引用片段时在句末标注编号，例如 [1]；"
                            "片段里没有的信息不要编造。\n\n" + "\n\n---\n\n".join(blocks)
                        ),
                    ),
                )

    messages.append(ChatMessage(role="user", content=question))

    impl = real_llm if use_real else mock_llm

    async def _collect() -> tuple[str, str, int]:
        chunks: list[str] = []
        result = None
        async for piece in impl.stream_chat(config, messages, temperature=temperature, max_tokens=max_tokens):
            if isinstance(piece, str):
                chunks.append(piece)
            else:
                result = piece
        return "".join(chunks), (result.mode if result else "mock"), (result.latency_ms if result else 0)

    text, mode, latency_ms = asyncio.run(_collect())
    del latency_ms
    return text, citations, mode, config.model


def run_cases(
    session: Session,
    *,
    prompt: str,
    cases: list[models.EvalCase],
    kb_id: str | None,
    threshold: float = 0.6,
    top_k: int = 4,
    temperature: float = 0.2,
    max_tokens: int = 400,
    prompt_id: str | None = None,
    note: str = "",
) -> models.EvalRun:
    """逐条跑评测并落库。同步执行 —— 单用户练手项目够用，真项目应放队列。"""
    started = time.perf_counter()

    run = models.EvalRun(
        id=f"eval-{uuid4().hex[:8]}",
        prompt_id=prompt_id,
        kb_id=kb_id,
        model="",
        mode="mock",
        total=len(cases),
        threshold=threshold,
        note=note,
        created_at=datetime.now(UTC).replace(microsecond=0),
    )
    session.add(run)
    session.commit()

    passed = 0
    score_sum = 0.0
    last_mode = "mock"
    last_model = ""

    for case in cases:
        case_started = time.perf_counter()
        points = split_points(case.expected)
        answer = ""
        citations: list[dict] = []
        mode = "mock"
        error: str | None = None

        try:
            answer, citations, mode, last_model = _sse_answer(
                session,
                prompt=prompt,
                question=case.question,
                kb_id=kb_id or case.kb_id,
                top_k=top_k,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            last_mode = mode
        except LLMError as exc:
            error = str(exc)
            answer = f"[调用失败] {error}"

        matched, missing = score_answer(answer, points)
        score = round(len(matched) / len(points), 3) if points else 0.0
        ok = bool(points) and score >= threshold
        if ok:
            passed += 1
        score_sum += score

        session.add(
            models.EvalResult(
                id=f"er-{uuid4().hex[:8]}",
                run_id=run.id,
                case_id=case.id,
                question=case.question,
                answer=answer[:4000],
                matched=len(matched),
                total_points=len(points),
                score=score,
                passed=ok,
                missing="｜".join(missing)[:800],
                latency_ms=int((time.perf_counter() - case_started) * 1000),
                citations=json.dumps(citations, ensure_ascii=False) if citations else None,
                created_at=datetime.now(UTC).replace(microsecond=0),
            )
        )
        session.commit()

    run.passed = passed
    run.avg_score = round(score_sum / len(cases), 3) if cases else 0.0
    run.mode = last_mode
    run.model = last_model
    run.took_ms = int((time.perf_counter() - started) * 1000)
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def list_results(session: Session, run_id: str) -> list[models.EvalResult]:
    return list(
        session.exec(
            select(models.EvalResult)
            .where(models.EvalResult.run_id == run_id)
            .order_by(models.EvalResult.created_at)
        ).all()
    )
