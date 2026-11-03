"""埋点与会话落库。

P1 的核心：**每一次真实调用都写一条 trace，每一次交互都写一条会话**。
LLMOps 的所有聚合、Agent 的运行历史、差评归因，都建立在这两张表上。

设计取舍：这里全部用调用方传进来的 Session，不自己开连接 ——
流式响应里会单独开一个 Session（见 chat.py），避免请求作用域的 session 提前关闭。
"""

from datetime import UTC, date, datetime
from uuid import uuid4

from sqlmodel import Session

from app import models

# 每 1K token 的美元单价（prompt, completion）。
# 真项目应从厂商目录或配置表读，这里写死一张小表够用。
PRICE_PER_1K: dict[str, tuple[float, float]] = {
    "deepseek-chat": (0.00014, 0.00028),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4o": (0.005, 0.015),
    "claude-3-5-sonnet": (0.003, 0.015),
}

# 未知模型不猜价格：按 0 计，但 trace 里保留 token 数，事后可以重算
FALLBACK_PRICE: tuple[float, float] = (0.0, 0.0)


def cost_for(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    price_in, price_out = PRICE_PER_1K.get(model, FALLBACK_PRICE)
    return round(prompt_tokens / 1000 * price_in + completion_tokens / 1000 * price_out, 6)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def start_conversation(
    session: Session,
    *,
    source: str,
    title: str = "",
    prompt_id: str | None = None,
    agent_id: str | None = None,
    app_id: str | None = None,
    workflow_id: str | None = None,
) -> models.Conversation:
    conversation = models.Conversation(
        id=new_id("conv"),
        title=title[:120],
        source=source,
        prompt_id=prompt_id,
        agent_id=agent_id,
        app_id=app_id,
        workflow_id=workflow_id,
    )
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def append_message(
    session: Session,
    conversation: models.Conversation,
    *,
    role: str,
    content: str,
    tokens: int = 0,
    latency_ms: int = 0,
    mode: str = "mock",
) -> models.Message:
    message = models.Message(
        id=new_id("msg"),
        conversation_id=conversation.id,
        role=role,
        content=content,
        tokens=tokens,
        latency_ms=latency_ms,
        mode=mode,
    )
    session.add(message)

    conversation.message_count += 1
    conversation.total_tokens += tokens
    conversation.updated_at = datetime.now(UTC).replace(microsecond=0)
    if not conversation.title and role == "user":
        conversation.title = content.strip().replace("\n", " ")[:60]
    session.add(conversation)

    session.commit()
    session.refresh(message)
    return message


def record_trace(
    session: Session,
    *,
    kind: str,
    provider: str,
    model: str,
    mode: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: int,
    status: str = "成功",
    error: str | None = None,
    conversation_id: str | None = None,
    agent_id: str | None = None,
    app_id: str | None = None,
    workflow_id: str | None = None,
) -> models.Trace:
    now = datetime.now(UTC).replace(microsecond=0)
    trace = models.Trace(
        id=new_id("tr"),
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost_for(model, prompt_tokens, completion_tokens),
        latency_ms=latency_ms,
        status=status,
        kind=kind,
        mode=mode,
        error=error[:400] if error else None,
        conversation_id=conversation_id,
        agent_id=agent_id,
        app_id=app_id,
        workflow_id=workflow_id,
        day=date.today(),
        created_at=now,
    )
    session.add(trace)

    # 会话上的累计成本同步更新，列表页不用再 join traces
    if conversation_id:
        conversation = session.get(models.Conversation, conversation_id)
        if conversation is not None:
            conversation.total_cost_usd = round(conversation.total_cost_usd + trace.cost_usd, 6)
            conversation.updated_at = now
            session.add(conversation)

    session.commit()
    session.refresh(trace)
    return trace
