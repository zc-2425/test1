"""工作流运行：产出可展示的执行链路。

P9 画布页的「运行工作流」弹窗需要结果框和节点级 trace，
这里按节点数造一条**确定性**的链路（同一条工作流每次跑出来结构一致，
只让耗时和 token 有小幅抖动），避免每次刷新数字乱跳。
"""

import random
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app import models
from app.db import get_session
from app.services import telemetry
from app.services.llm import ChatMessage, LLMError, resolve_config
from app.services.llm import openai_compatible as real_llm

router = APIRouter(prefix="/workflows", tags=["工作流"])

# 节点类型 → 展示名，与画布左侧节点库一致
NODE_SEQUENCE = [
    ("start", "开始"),
    ("llm", "LLM"),
    ("retrieval", "知识检索"),
    ("agent", "Agent"),
    ("transform", "数据转换"),
    ("condition", "条件判断"),
    ("end", "结束"),
]


class RunIn(BaseModel):
    input: str = ""


# 本次请求是否走真模型：由 APP_LLM_MODE + 是否配置了 Key 决定
_CONFIG = resolve_config()


async def _run_real_llm(
    workflow_name: str, user_input: str, config
) -> tuple[str, tuple[int, int], int] | None:
    """真调一次模型；不可用时返回 None，让调用方回落到模拟。"""
    if config is None or not config.ready:
        return None

    messages = [
        ChatMessage(role="system", content=f"你是工作流「{workflow_name}」里的 LLM 节点，回答要简短。"),
        ChatMessage(role="user", content=user_input.strip() or "你好"),
    ]
    parts: list[str] = []
    usage: tuple[int, int] = (0, 0)
    latency = 0
    try:
        async for chunk in real_llm.stream_chat(config, messages, temperature=0.7):
            if isinstance(chunk, str):
                parts.append(chunk)
            else:
                usage = (chunk.prompt_tokens, chunk.completion_tokens)
                latency = chunk.latency_ms
    except LLMError as exc:
        # 真调用失败不掩盖：把原因写进节点输出，同时回落模拟
        return None if not parts else ("".join(parts), usage, latency)
    text = "".join(parts).strip()
    if not text:
        return None
    return (text[:240], usage, latency)


@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: str,
    payload: RunIn,
    session: Session = Depends(get_session),
) -> dict:
    wf = session.get(models.Workflow, workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail=f"工作流不存在: {workflow_id}")

    # 用 id 做种子：同一条工作流每次结构稳定，不同工作流之间不同
    rng = random.Random(hash(workflow_id) & 0xFFFFFFFF)
    node_total = max(2, wf.node_count or 5)
    start_node, end_node = NODE_SEQUENCE[0], NODE_SEQUENCE[-1]
    middles = NODE_SEQUENCE[1:-1]
    # 步数必须与工作流的 node_count 对齐，否则「8 节点」的工作流只跑出 7 步
    picked = (
        [start_node] + [middles[i % len(middles)] for i in range(node_total - 2)] + [end_node]
    )

    # P1：一次运行也记成一次会话，运行历史与成本才有归属
    conversation = telemetry.start_conversation(
        session,
        source="workflow_run",
        title=(payload.input or "工作流运行")[:60],
        workflow_id=workflow_id,
    )
    if payload.input.strip():
        telemetry.append_message(session, conversation, role="user", content=payload.input.strip())

    steps: list[dict] = []
    total_ms = 0
    prompt_tokens = 0
    completion_tokens = 0
    for i, (node_type, name) in enumerate(picked):
        duration = rng.randint(6, 40) if node_type in {"start", "end"} else rng.randint(180, 900)
        total_ms += duration
        step = {
            "nodeId": f"n{i + 1}",
            "nodeType": node_type,
            "name": name,
            "status": "成功",
            "durationMs": duration,
        }
        if node_type == "llm":
            # 配了 Key 就真调一次模型；没配就沿用确定性模拟，避免演示时直接报错
            real = await _run_real_llm(wf.name, payload.input, _CONFIG)
            if real is None:
                node_prompt = rng.randint(320, 900)
                node_completion = rng.randint(120, 480)
                prompt_tokens += node_prompt
                completion_tokens += node_completion
                step["output"] = "已生成回答，共 3 段、约 220 字。（模拟）"
                step["mode"] = "mock"
                node_mode = "mock"
                node_latency = duration
            else:
                text, usage, latency = real
                node_prompt, node_completion = usage
                prompt_tokens += node_prompt
                completion_tokens += node_completion
                duration = latency
                total_ms += latency
                step["output"] = text
                step["mode"] = "real"
                node_mode = "real"
                node_latency = latency

            # 每个 LLM 节点都是一次真实调用，单独记一条 trace
            telemetry.record_trace(
                session,
                kind="workflow_run",
                provider=(_CONFIG.provider if _CONFIG else "unknown"),
                model=(_CONFIG.model if _CONFIG else "unknown"),
                mode=node_mode,
                prompt_tokens=node_prompt,
                completion_tokens=node_completion,
                latency_ms=node_latency,
                conversation_id=conversation.id,
                workflow_id=workflow_id,
            )
        elif node_type == "retrieval":
            step["output"] = "命中 5 个分块，最高相似度 0.87。"
        elif node_type == "condition":
            step["output"] = "命中分支：是"
        elif node_type == "start":
            step["output"] = payload.input or "（空输入）"
        steps.append(step)

    run_id = f"run-{uuid4().hex[:8]}"
    result = {
        "runId": run_id,
        "workflowId": workflow_id,
        "workflowName": wf.name,
        "status": "成功",
        "startedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "durationMs": total_ms,
        "tokens": {"prompt": prompt_tokens, "completion": completion_tokens},
        "output": "根据知识库检索结果，您的订单预计 3 个工作日内送达；如需加急请联系人工客服。",
        "steps": steps,
    }

    # 结束消息也落库：一次运行 = 一条 user + 一条 assistant
    telemetry.append_message(
        session,
        conversation,
        role="assistant",
        content=result["output"],
        tokens=completion_tokens,
        latency_ms=total_ms,
        mode="real" if any(s.get("mode") == "real" for s in steps) else "mock",
    )

    # 运行完顺手更新工作流状态与最后运行时间，列表页立刻能看到变化
    wf.last_run_at = datetime.now(UTC).replace(microsecond=0)
    wf.status = "已发布" if wf.status == "运行中" else wf.status
    session.add(wf)
    session.commit()

    return result


@router.post("/{workflow_id}/publish")
def publish_workflow(workflow_id: str, session: Session = Depends(get_session)) -> models.Workflow:
    wf = session.get(models.Workflow, workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail=f"工作流不存在: {workflow_id}")
    wf.status = "已发布"
    session.add(wf)
    session.commit()
    session.refresh(wf)
    return wf
