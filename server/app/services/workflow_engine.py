"""工作流执行引擎（R4）。

前面 12 个阶段的 `/run` 是**按 node_count 编出来的假的**：步数对了，但没有任何东西被执行。
这里换成真的：读库里的节点与连线，从 start 开始沿边逐个执行，每个节点都留下真实的输入输出。

执行语义（刻意保持简单，够用且看得懂）：
- 上下文 ctx 是一个变量字典：query（用户输入）+ 各节点 config.output 指定的变量
- start      → ctx.query
- llm        → 真调模型（system 来自节点配置），输出写入 config.output（默认 llm_output）
- retrieval  → 真检索（config.knowledge 指向知识库），命中片段写入 config.output
- qa         → 用 question 模板 + 上下文变量再问一次模型，输出写入 config.output
- transform  → 模板替换 {{var}}
- condition  → 求值 config.expression，根据 true/false 选下一条边
- agent / code / http → **未接入执行体**，如实标注「跳过」而不是假装跑过
- end        → 最终输出

沿边推进时每个节点只执行一次（visited），步数上限 50，避免环。
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from sqlmodel import Session, select

from app import models
from app.services import rag, telemetry
from app.services.llm import ChatMessage, LLMError, resolve_config, should_use_real
from app.services.llm import mock as mock_llm
from app.services.llm import openai_compatible as real_llm

MAX_STEPS = 50
_VAR = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

# 这些类型没有真实执行体：接入工具沙箱/代码执行前，如实标注跳过
UNSUPPORTED = {
    "agent": "Agent 运行时未接入（R5）",
    "code": "代码执行沙箱未接入（R5）",
    "http": "HTTP 节点执行器未接入（R5）",
    "tool": "工具执行器未接入（R5）",
}


def load_graph(
    session: Session, workflow_id: str
) -> tuple[list[models.WorkflowNode], list[models.WorkflowEdge]]:
    nodes = list(
        session.exec(
            select(models.WorkflowNode)
            .where(models.WorkflowNode.workflow_id == workflow_id)
            .order_by(models.WorkflowNode.order)
        ).all()
    )
    edges = list(
        session.exec(
            select(models.WorkflowEdge).where(models.WorkflowEdge.workflow_id == workflow_id)
        ).all()
    )
    return nodes, edges


def save_graph(
    session: Session, workflow_id: str, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]
) -> tuple[int, int]:
    """整图覆盖保存：先删后插，避免增量 diff 出错。"""
    for row in session.exec(
        select(models.WorkflowNode).where(models.WorkflowNode.workflow_id == workflow_id)
    ).all():
        session.delete(row)
    for row in session.exec(
        select(models.WorkflowEdge).where(models.WorkflowEdge.workflow_id == workflow_id)
    ).all():
        session.delete(row)
    session.commit()

    for index, node in enumerate(nodes):
        session.add(
            models.WorkflowNode(
                id=str(node.get("id")),
                workflow_id=workflow_id,
                type=str(node.get("type") or "llm"),
                name=str(node.get("name") or ""),
                x=float(node.get("x") or 0),
                y=float(node.get("y") or 0),
                config=json.dumps(node.get("config") or {}, ensure_ascii=False),
                order=index,
            )
        )
    for edge in edges:
        session.add(
            models.WorkflowEdge(
                id=str(edge.get("id")),
                workflow_id=workflow_id,
                source=str(edge.get("from") or edge.get("source") or ""),
                target=str(edge.get("to") or edge.get("target") or ""),
                label=str(edge.get("label") or ""),
            )
        )
    session.commit()

    wf = session.get(models.Workflow, workflow_id)
    if wf is not None:
        wf.node_count = len(nodes)
        session.add(wf)
        session.commit()

    return len(nodes), len(edges)


def _cfg(node: models.WorkflowNode) -> dict[str, Any]:
    try:
        data = json.loads(node.config or "{}")
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _render(template: str, ctx: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        return str(ctx.get(match.group(1), ""))

    return _VAR.sub(replace, template)


def _evaluate(expression: str, ctx: dict[str, Any]) -> bool:
    """只支持几种可解释的写法，不做任意表达式求值（安全）。

    - contains:关键词
    - equals:a==b
    - empty / notempty
    缺省：上一个输出非空即为 true。
    """
    expr = (expression or "").strip()
    last = str(ctx.get("last_output", ""))
    if not expr:
        return bool(last.strip())

    if expr.startswith("contains:"):
        return expr[len("contains:") :] in str(ctx.get("query", "")) or expr[len("contains:") :] in last
    if expr.startswith("equals:"):
        body = expr[len("equals:") :]
        left, _, right = body.partition("==")
        return str(ctx.get(left.strip(), "")).strip() == right.strip()
    if expr == "empty":
        return not last.strip()
    if expr == "notempty":
        return bool(last.strip())
    return bool(last.strip())


def _pick_next(node: models.WorkflowNode, edges: list[models.WorkflowEdge], result: bool) -> str | None:
    outgoing = [edge for edge in edges if edge.source == node.id]
    if not outgoing:
        return None
    if node.type == "condition":
        # 只有一条出边时没得选：条件只影响输出文本，不影响走向
        if len(outgoing) == 1:
            return outgoing[0].target
        # 先按 label 找 true / false 分支
        wanted = "true" if result else "false"
        for edge in outgoing:
            if edge.label.strip().lower() == wanted:
                return edge.target
        # 没配 label 时：true 走第一条，false 走第二条
        if result:
            return outgoing[0].target
        return outgoing[1].target if len(outgoing) > 1 else None
    return outgoing[0].target


async def _run_llm(
    config_text: str, question: str, ctx: dict[str, Any]
) -> tuple[str, str, int, int, int]:
    """返回 (文本, mode, prompt_tokens, completion_tokens, latency_ms)。"""
    config = resolve_config()
    if config is None:
        raise LLMError("没有可用的模型配置")

    impl = real_llm if should_use_real() else mock_llm
    messages = []
    if config_text.strip():
        messages.append(ChatMessage(role="system", content=_render(config_text, ctx)))
    messages.append(ChatMessage(role="user", content=question))

    chunks: list[str] = []
    result = None
    async for piece in impl.stream_chat(config, messages, temperature=0.3, max_tokens=400):
        if isinstance(piece, str):
            chunks.append(piece)
        else:
            result = piece

    text = "".join(chunks).strip()
    if result is None:
        return text, "mock", 0, 0, 0
    return text, result.mode, result.prompt_tokens, result.completion_tokens, result.latency_ms


async def execute(
    session: Session, workflow: models.Workflow, user_input: str
) -> dict[str, Any]:
    nodes, edges = load_graph(session, workflow.id)
    if not nodes:
        raise ValueError("这个工作流还没有节点，先在画布上保存一次")

    by_id = {node.id: node for node in nodes}
    start = next((node for node in nodes if node.type == "start"), nodes[0])

    conversation = telemetry.start_conversation(
        session,
        source="workflow_run",
        title=(user_input or "工作流运行")[:60],
        workflow_id=workflow.id,
    )
    telemetry.append_message(session, conversation, role="user", content=user_input or "（空输入）")

    ctx: dict[str, Any] = {"query": user_input, "last_output": user_input}
    steps: list[dict[str, Any]] = []
    citations: list[dict[str, Any]] = []
    prompt_tokens = 0
    completion_tokens = 0
    total_ms = 0
    final_output = ""

    current: models.WorkflowNode | None = start
    visited: set[str] = set()
    step_no = 0

    while current is not None and step_no < MAX_STEPS:
        if current.id in visited:
            break
        visited.add(current.id)
        step_no += 1

        config = _cfg(current)
        started = time.perf_counter()
        status = "成功"
        output = ""
        mode = "mock"
        node_citations: list[dict[str, Any]] = []

        try:
            if current.type == "start":
                output = user_input or "（空输入）"

            elif current.type == "llm":
                output, mode, pt, ct, latency = await _run_llm(
                    str(config.get("system") or ""), user_input or "你好", ctx
                )
                prompt_tokens += pt
                completion_tokens += ct
                total_ms += latency
                variable = str(config.get("output") or "llm_output")
                ctx[variable] = output

            elif current.type == "retrieval":
                kb_id = str(config.get("knowledge") or "")
                kb = session.get(models.KnowledgeBase, kb_id) if kb_id else None
                if kb is None:
                    status = "跳过"
                    output = "未绑定知识库（节点配置里的 knowledge 为空）"
                else:
                    top_k = int(config.get("topK") or 4)
                    found = rag.search(session, kb, user_input or "你好", top_k)
                    node_citations = found["hits"]
                    citations = found["hits"] if not citations else citations
                    if node_citations:
                        output = "\n\n".join(
                            f"[{i + 1}] {hit['docName']} 第 {hit['position'] + 1} 段（{hit['score']}）\n{hit['preview']}"
                            for i, hit in enumerate(node_citations)
                        )
                    else:
                        status = "跳过"
                        output = "知识库里没有命中"
                    ctx[str(config.get("output") or "chunks")] = output

            elif current.type == "qa":
                template = str(config.get("question") or "{{query}}")
                question = _render(template, ctx)
                context_var = str(config.get("context") or "chunks")
                context_text = str(ctx.get(context_var, ""))
                if context_text:
                    question = f"参考资料：\n{context_text}\n\n问题：{question}"
                output, mode, pt, ct, latency = await _run_llm("回答要简洁，必要时标注引用编号。", question, ctx)
                prompt_tokens += pt
                completion_tokens += ct
                total_ms += latency
                ctx[str(config.get("output") or "answer")] = output

            elif current.type == "transform":
                template = str(config.get("template") or "{{last_output}}")
                output = _render(template, ctx)
                ctx[str(config.get("output") or "transformed")] = output

            elif current.type == "condition":
                passed = _evaluate(str(config.get("expression") or ""), ctx)
                status = "成功"
                output = "命中分支：是" if passed else "命中分支：否"
                ctx["condition"] = passed
                ctx[str(config.get("output") or "condition_result")] = passed

            elif current.type in UNSUPPORTED:
                status = "跳过"
                output = UNSUPPORTED[current.type]

            elif current.type == "end":
                # 结束节点输出「流进来的那个值」，而不是回头去翻更早的 answer 变量
                output = str(
                    ctx.get("last_output") or ctx.get("answer") or ctx.get("llm_output") or ""
                )

            else:
                status = "跳过"
                output = f"未知节点类型：{current.type}"

        except LLMError as exc:
            status = "失败"
            output = f"[调用失败] {exc}"
        except Exception as exc:  # noqa: BLE001 - 单个节点失败不应炸掉整个运行
            status = "失败"
            output = f"[异常] {exc}"

        duration = int((time.perf_counter() - started) * 1000)

        if current.type in {"llm", "qa"}:
            telemetry.record_trace(
                session,
                kind="workflow_run",
                provider=(resolve_config().provider if resolve_config() else "unknown"),
                model=(resolve_config().model if resolve_config() else "unknown"),
                mode=mode,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=duration,
                status="失败" if status == "失败" else "成功",
                error=output if status == "失败" else None,
                conversation_id=conversation.id,
                workflow_id=workflow.id,
            )

        steps.append(
            {
                "nodeId": current.id,
                "nodeType": current.type,
                "name": config.get("name") or current.name or current.type,
                "status": status,
                "durationMs": duration,
                "output": output[:600],
                "mode": mode if current.type in {"llm", "qa"} else None,
            }
        )

        ctx["last_output"] = output
        if current.type == "end":
            final_output = output
            break

        next_id = _pick_next(current, edges, bool(ctx.get("condition", True)))
        current = by_id.get(next_id) if next_id else None

    if not final_output:
        final_output = str(ctx.get("last_output") or "")

    telemetry.append_message(
        session,
        conversation,
        role="assistant",
        content=final_output or "（本次运行没有产生输出）",
        tokens=completion_tokens,
        latency_ms=total_ms,
        mode="real" if any(step.get("mode") == "real" for step in steps) else "mock",
        citations=citations or None,
    )

    workflow.last_run_at = __import__("datetime").datetime.now(__import__("datetime").UTC).replace(
        microsecond=0
    )
    session.add(workflow)
    session.commit()

    return {
        "runId": telemetry.new_id("run"),
        "workflowId": workflow.id,
        "workflowName": workflow.name,
        "status": "成功" if all(step["status"] != "失败" for step in steps) else "失败",
        "startedAt": __import__("datetime").datetime.now(__import__("datetime").UTC)
        .replace(microsecond=0)
        .isoformat(),
        "durationMs": sum(step["durationMs"] for step in steps),
        "tokens": {"prompt": prompt_tokens, "completion": completion_tokens},
        "output": final_output,
        "steps": steps,
        "citations": citations,
        "conversationId": conversation.id,
    }
