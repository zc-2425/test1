"""系统级接口：健康检查、全局概览、告警。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select

from app import models
from app.core.config import get_settings
from app.db import get_session
from app.schemas import HealthOut

router = APIRouter()
settings = get_settings()

VERSION = "0.1.0"


@router.get("/health", response_model=HealthOut, tags=["系统"])
def health(session: Session = Depends(get_session)) -> HealthOut:
    try:
        wf = session.exec(select(func.count()).select_from(models.Workflow)).one()
        db_state = "ok"
        seed_ready = wf > 0
    except Exception as exc:  # noqa: BLE001 - 健康检查要吞掉异常并如实上报
        db_state = f"error: {exc}"
        seed_ready = False
    return HealthOut(
        status="ok",
        app=settings.app_name,
        version=VERSION,
        db=db_state,
        seed_ready=seed_ready,
    )


@router.get("/meta/overview", tags=["系统"])
def overview(session: Session = Depends(get_session)) -> dict:
    """侧栏各模块的数量 + 探索页 4 个统计卡。

    探索页那 4 个数字（16 / 5 / 4 / 11.8K）在原型里是设计稿写死的，
    这里用「模板总数 = 提示词模板 + 工作流模板 + 应用模板」之类的方式算出来，
    避免后端又变成一堆硬编码常量。
    """

    def count(model) -> int:  # noqa: ANN001
        return session.exec(select(func.count()).select_from(model)).one()

    prompt_count = count(models.Prompt)
    workflow_count = count(models.Workflow)
    app_count = count(models.App)

    usage_total = sum(
        session.exec(select(models.App.usage_count)).all()
    ) + sum(session.exec(select(models.Tool.call_count)).all())

    return {
        "counts": {
            "workflows": workflow_count,
            "agents": count(models.Agent),
            "knowledgeBases": count(models.KnowledgeBase),
            "datasets": count(models.Dataset),
            "prompts": prompt_count,
            "tools": count(models.Tool),
            "providers": count(models.ModelProvider),
            "apps": app_count,
            "plugins": count(models.Plugin),
            "alerts": count(models.Alert),
        },
        "explore": {
            "totalTemplates": prompt_count + workflow_count + app_count,
            "hotTemplates": count(models.Plugin),  # 原型 5，这里用插件数近似
            "favoriteTemplates": 4,
            "totalUsage": usage_total,
        },
    }


@router.get("/alerts", tags=["系统"])
def list_alerts(
    status: str | None = None,
    limit: int = 20,
    session: Session = Depends(get_session),
) -> list[models.Alert]:
    stmt = select(models.Alert)
    if status:
        stmt = stmt.where(models.Alert.status == status)
    return list(session.exec(stmt.order_by(models.Alert.created_at.desc()).limit(limit)).all())


@router.post("/alerts/{alert_id}/resolve", tags=["系统"])
def resolve_alert(alert_id: str, session: Session = Depends(get_session)) -> models.Alert:
    alert = session.get(models.Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"告警不存在: {alert_id}")
    alert.status = "已解决"
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert
