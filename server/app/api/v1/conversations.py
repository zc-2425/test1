"""会话与调用记录的查询接口。

P1 之前这些数据是种子；现在它们由真实交互产生，所以需要能查、能删。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, func, select

from app import models
from app.db import get_session
from app.schemas import Page

router = APIRouter(tags=["会话与调用"])


@router.get("/conversations", response_model=Page[models.Conversation])
def list_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    source: str | None = Query(None, description="prompt_test / workflow_run / app_chat"),
    prompt_id: str | None = None,
    agent_id: str | None = None,
    app_id: str | None = None,
    workflow_id: str | None = None,
    session: Session = Depends(get_session),
):
    stmt = select(models.Conversation)
    for field_name, value in (
        ("source", source),
        ("prompt_id", prompt_id),
        ("agent_id", agent_id),
        ("app_id", app_id),
        ("workflow_id", workflow_id),
    ):
        if value:
            stmt = stmt.where(getattr(models.Conversation, field_name) == value)

    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    rows = session.exec(
        stmt.order_by(models.Conversation.updated_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return {"items": rows, "total": total, "page": page, "size": size}


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str, session: Session = Depends(get_session)
) -> dict:
    conversation = session.get(models.Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail=f"会话不存在: {conversation_id}")

    messages = session.exec(
        select(models.Message)
        .where(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.created_at)
    ).all()
    traces = session.exec(
        select(models.Trace)
        .where(models.Trace.conversation_id == conversation_id)
        .order_by(models.Trace.created_at)
    ).all()

    return {
        "conversation": conversation,
        "messages": messages,
        "traces": traces,
    }


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, session: Session = Depends(get_session)) -> None:
    conversation = session.get(models.Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail=f"会话不存在: {conversation_id}")

    for message in session.exec(
        select(models.Message).where(models.Message.conversation_id == conversation_id)
    ).all():
        session.delete(message)
    for trace in session.exec(
        select(models.Trace).where(models.Trace.conversation_id == conversation_id)
    ).all():
        session.delete(trace)

    session.delete(conversation)
    session.commit()


@router.get("/traces", response_model=Page[models.Trace])
def list_traces(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    kind: str | None = None,
    mode: str | None = None,
    status: str | None = None,
    conversation_id: str | None = None,
    session: Session = Depends(get_session),
):
    stmt = select(models.Trace)
    for field_name, value in (
        ("kind", kind),
        ("mode", mode),
        ("status", status),
        ("conversation_id", conversation_id),
    ):
        if value:
            stmt = stmt.where(getattr(models.Trace, field_name) == value)

    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    rows = session.exec(
        stmt.order_by(models.Trace.created_at.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return {"items": rows, "total": total, "page": page, "size": size}
