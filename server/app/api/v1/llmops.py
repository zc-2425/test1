"""LLMOps 监控的聚合接口。

关键点：所有数字都从 traces 表算出来，不写死常数。
原型里 71.2% 与 78% 两处「同一个指标不同值」的 bug，就是因为写死了两份。
"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, select

from app import models
from app.db import get_session

router = APIRouter(prefix="/llmops", tags=["LLMOps监控"])


@router.get("/overview")
def ops_overview(session: Session = Depends(get_session)) -> dict:
    total_calls = session.exec(select(func.count()).select_from(models.Trace)).one()
    success_calls = session.exec(
        select(func.count()).select_from(models.Trace).where(models.Trace.status == "成功")
    ).one()
    avg_latency = session.exec(select(func.avg(models.Trace.latency_ms))).one()
    total_cost = session.exec(select(func.sum(models.Trace.cost_usd))).one()
    total_tokens = session.exec(
        select(func.sum(models.Trace.prompt_tokens) + func.sum(models.Trace.completion_tokens))
    ).one()
    active_alerts = session.exec(
        select(func.count()).select_from(models.Alert).where(models.Alert.status == "未处理")
    ).one()

    providers = session.exec(select(models.ModelProvider)).all()
    alerts = session.exec(
        select(models.Alert).order_by(models.Alert.created_at.desc()).limit(3)
    ).all()

    return {
        "cards": {
            "totalCalls": total_calls,
            "successRate": round((success_calls / total_calls * 100) if total_calls else 0, 1),
            "avgLatencyMs": round(avg_latency or 0),
            "totalCostUsd": round(total_cost or 0, 2),
            "totalTokens": total_tokens or 0,
            "activeAlerts": active_alerts,
        },
        "health": [
            {
                "id": p.id,
                "name": p.name,
                "status": p.status,
                "modelCount": p.model_count,
                "enabled": p.enabled,
            }
            for p in providers
        ],
        "recentAlerts": alerts,
    }


@router.get("/cost/series")
def cost_series(
    days: int = Query(15, ge=1, le=90), session: Session = Depends(get_session)
) -> dict:
    """按天 × 模型聚合成本，前端画折线 + 堆叠用。"""
    rows = session.exec(
        select(
            models.Trace.day,
            models.Trace.model,
            func.sum(models.Trace.cost_usd).label("cost"),
            func.count().label("calls"),
        )
        .group_by(models.Trace.day, models.Trace.model)
        .order_by(models.Trace.day)
    ).all()

    by_day: dict[str, dict[str, float]] = {}
    models_seen: set[str] = set()
    for day, model_name, cost, _calls in rows:
        key = day.isoformat()
        by_day.setdefault(key, {"day": key, "total": 0.0})  # type: ignore[arg-type]
        by_day[key][model_name] = round(float(cost or 0), 4)
        by_day[key]["total"] = round(by_day[key]["total"] + float(cost or 0), 4)
        models_seen.add(model_name)

    series = sorted(by_day.values(), key=lambda x: x["day"])[-days:]
    return {"models": sorted(models_seen), "series": series}


@router.get("/models")
def model_perf(session: Session = Depends(get_session)) -> list[dict]:
    rows = session.exec(
        select(
            models.Trace.model,
            func.count().label("calls"),
            func.avg(models.Trace.latency_ms).label("avg_latency"),
            func.sum(models.Trace.cost_usd).label("cost"),
            func.sum(models.Trace.prompt_tokens + models.Trace.completion_tokens).label("tokens"),
        ).group_by(models.Trace.model)
    ).all()

    result: list[dict] = []
    for model_name, calls, avg_latency, cost, tokens in rows:
        ok = session.exec(
            select(func.count())
            .select_from(models.Trace)
            .where(models.Trace.model == model_name)
            .where(models.Trace.status == "成功")
        ).one()
        result.append(
            {
                "model": model_name,
                "calls": calls,
                "successRate": round(ok / calls * 100, 1) if calls else 0.0,
                "avgLatencyMs": round(float(avg_latency or 0)),
                "totalCostUsd": round(float(cost or 0), 2),
                "totalTokens": int(tokens or 0),
            }
        )
    return sorted(result, key=lambda x: x["calls"], reverse=True)


@router.get("/ab-tests")
def ab_tests(session: Session = Depends(get_session)) -> list[models.AbTest]:
    return list(
        session.exec(select(models.AbTest).order_by(models.AbTest.started_at.desc())).all()
    )
