"""评测接口：用例 CRUD + 跑一次评测 + 历史对比。

评测是同步跑的（逐条调模型），单用户练手项目够用；
真项目应该丢进任务队列并在前端轮询进度。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app import models
from app.db import get_session
from app.services import evaluation

router = APIRouter(prefix="/eval", tags=["评测"])


class CaseIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    expected: str = ""
    prompt_id: str | None = None
    kb_id: str | None = None
    enabled: bool = True


class CasePatch(BaseModel):
    question: str | None = None
    expected: str | None = None
    kb_id: str | None = None
    enabled: bool | None = None


class RunIn(BaseModel):
    prompt_id: str | None = None
    # 提示词正文由前端传入：评测的就是「当前编辑器里的内容」，不必先保存
    prompt: str = ""
    kb_id: str | None = None
    threshold: float = Field(default=0.6, ge=0, le=1)
    max_tokens: int = Field(default=400, ge=32, le=2000)
    top_k: int = Field(default=4, ge=1, le=8)
    case_ids: list[str] | None = None
    note: str = ""


@router.get("/cases", response_model=list[models.EvalCase])
def list_cases(
    prompt_id: str | None = Query(None),
    kb_id: str | None = Query(None),
    session: Session = Depends(get_session),
):
    stmt = select(models.EvalCase)
    if prompt_id:
        stmt = stmt.where(models.EvalCase.prompt_id == prompt_id)
    if kb_id:
        stmt = stmt.where(models.EvalCase.kb_id == kb_id)
    return list(session.exec(stmt.order_by(models.EvalCase.created_at)).all())


@router.post("/cases", status_code=201, response_model=models.EvalCase)
def create_case(
    payload: CaseIn, session: Session = Depends(get_session)
) -> models.EvalCase:
    case = models.EvalCase(
        id=f"case-{__import__('uuid').uuid4().hex[:8]}",
        question=payload.question.strip(),
        expected=payload.expected.strip(),
        prompt_id=payload.prompt_id,
        kb_id=payload.kb_id,
        enabled=payload.enabled,
    )
    session.add(case)
    session.commit()
    session.refresh(case)
    return case


@router.patch("/cases/{case_id}", response_model=models.EvalCase)
def update_case(
    case_id: str, payload: CasePatch, session: Session = Depends(get_session)
) -> models.EvalCase:
    case = session.get(models.EvalCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"用例不存在: {case_id}")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    session.add(case)
    session.commit()
    session.refresh(case)
    return case


@router.delete("/cases/{case_id}", status_code=204)
def delete_case(case_id: str, session: Session = Depends(get_session)) -> None:
    case = session.get(models.EvalCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"用例不存在: {case_id}")
    session.delete(case)
    session.commit()


@router.post("/runs", status_code=201)
def create_run(payload: RunIn, session: Session = Depends(get_session)) -> dict:
    cases = evaluation_scope(session, payload)
    if not cases:
        raise HTTPException(status_code=400, detail="没有可评测的用例，先添加几条")

    # 没传正文时按 prompt_id 取库里的提示词，前端就不必先读一遍
    prompt_text = payload.prompt
    if not prompt_text.strip() and payload.prompt_id:
        prompt_row = session.get(models.Prompt, payload.prompt_id)
        if prompt_row is not None:
            prompt_text = prompt_row.content

    run = evaluation.run_cases(
        session,
        prompt=prompt_text,
        cases=cases,
        kb_id=payload.kb_id,
        threshold=payload.threshold,
        max_tokens=payload.max_tokens,
        top_k=payload.top_k,
        prompt_id=payload.prompt_id,
        note=payload.note,
    )
    results = evaluation.list_results(session, run.id)
    return {"run": run, "results": results}


def evaluation_scope(session: Session, payload: RunIn) -> list[models.EvalCase]:
    stmt = select(models.EvalCase).where(models.EvalCase.enabled.is_(True))
    if payload.case_ids:
        stmt = stmt.where(models.EvalCase.id.in_(payload.case_ids))
    elif payload.prompt_id:
        stmt = stmt.where(models.EvalCase.prompt_id == payload.prompt_id)
    return list(session.exec(stmt.order_by(models.EvalCase.created_at)).all())


@router.get("/runs", response_model=list[models.EvalRun])
def list_runs(
    prompt_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    stmt = select(models.EvalRun)
    if prompt_id:
        stmt = stmt.where(models.EvalRun.prompt_id == prompt_id)
    return list(
        session.exec(stmt.order_by(models.EvalRun.created_at.desc()).limit(limit)).all()
    )


@router.get("/runs/{run_id}")
def get_run(run_id: str, session: Session = Depends(get_session)) -> dict:
    run = session.get(models.EvalRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"评测不存在: {run_id}")
    return {"run": run, "results": evaluation.list_results(session, run_id)}
