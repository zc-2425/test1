"""工作流运维接口：画布图的读写、运行、发布。

R4 起运行不再模拟：读库里的节点与连线，交给 services/workflow_engine 真跑。
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app import models
from app.db import get_session
from app.services import workflow_engine

router = APIRouter(prefix="/workflows", tags=["工作流"])


class RunIn(BaseModel):
    input: str = ""


class GraphNodeIn(BaseModel):
    id: str
    type: str
    name: str = ""
    x: float = 0
    y: float = 0
    config: dict[str, Any] = Field(default_factory=dict)


class GraphEdgeIn(BaseModel):
    id: str
    source: str | None = None
    target: str | None = None
    # 前端用的是 from / to
    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    label: str = ""


class GraphIn(BaseModel):
    nodes: list[GraphNodeIn] = Field(default_factory=list)
    edges: list[GraphEdgeIn] = Field(default_factory=list)


@router.get("/{workflow_id}/graph")
def get_graph(workflow_id: str, session: Session = Depends(get_session)) -> dict:
    workflow = session.get(models.Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"工作流不存在: {workflow_id}")

    nodes, edges = workflow_engine.load_graph(session, workflow_id)
    return {
        "workflowId": workflow_id,
        "nodes": [
            {
                "id": node.id,
                "type": node.type,
                "name": node.name,
                "x": node.x,
                "y": node.y,
                "config": json.loads(node.config or "{}"),
            }
            for node in nodes
        ],
        "edges": [
            {
                "id": edge.id,
                "from": edge.source,
                "to": edge.target,
                "label": edge.label,
            }
            for edge in edges
        ],
    }


@router.put("/{workflow_id}/graph")
def put_graph(
    workflow_id: str, payload: GraphIn, session: Session = Depends(get_session)
) -> dict:
    workflow = session.get(models.Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"工作流不存在: {workflow_id}")

    node_ids = [node.id for node in payload.nodes]
    for edge in payload.edges:
        source = edge.source or edge.from_
        target = edge.target or edge.to
        if source not in node_ids or target not in node_ids:
            raise HTTPException(
                status_code=400, detail=f"连线 {edge.id} 指向不存在的节点：{source} → {target}"
            )

    nodes = [
        {
            "id": node.id,
            "type": node.type,
            "name": node.name,
            "x": node.x,
            "y": node.y,
            "config": node.config,
        }
        for node in payload.nodes
    ]
    edges = [
        {
            "id": edge.id,
            "from": edge.source or edge.from_,
            "to": edge.target or edge.to,
            "label": edge.label,
        }
        for edge in payload.edges
    ]
    node_count, edge_count = workflow_engine.save_graph(session, workflow_id, nodes, edges)
    return {"nodes": node_count, "edges": edge_count}


@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: str,
    payload: RunIn,
    session: Session = Depends(get_session),
) -> dict:
    workflow = session.get(models.Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"工作流不存在: {workflow_id}")

    try:
        return await workflow_engine.execute(session, workflow, payload.input)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{workflow_id}/publish")
def publish_workflow(workflow_id: str, session: Session = Depends(get_session)) -> models.Workflow:
    workflow = session.get(models.Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"工作流不存在: {workflow_id}")

    nodes, _edges = workflow_engine.load_graph(session, workflow_id)
    if not nodes:
        raise HTTPException(status_code=400, detail="画布是空的，先保存节点再发布")

    workflow.status = "已发布"
    session.add(workflow)
    session.commit()
    session.refresh(workflow)
    return workflow
