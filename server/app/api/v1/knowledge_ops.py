"""知识库的异步操作：重建索引 / 向量化进度模拟。

P6 的详情页要展示「向量化处理中 65%」，所以进度必须真的会动。
这里用 FastAPI BackgroundTasks + asyncio 逐步推进，单用户场景足够；
真项目应该换任务队列（Celery / arq / RQ）。
"""

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session

from app import models
from app.db import engine, get_session

router = APIRouter(prefix="/knowledge-bases", tags=["知识库"])

STEPS = (20, 45, 70, 90, 100)
STEP_DELAY_SECONDS = 2.0


async def _advance_progress(kb_id: str) -> None:
    for value in STEPS:
        await asyncio.sleep(STEP_DELAY_SECONDS)
        with Session(engine) as session:
            kb = session.get(models.KnowledgeBase, kb_id)
            if kb is None:
                return
            kb.vector_progress = value
            kb.status = "已就绪" if value >= 100 else "处理中"
            session.add(kb)
            session.commit()


@router.post("/{kb_id}/reindex")
def reindex(
    kb_id: str,
    background: BackgroundTasks,
    session: Session = Depends(get_session),
) -> models.KnowledgeBase:
    kb = session.get(models.KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail=f"知识库不存在: {kb_id}")
    kb.status = "处理中"
    kb.vector_progress = 5
    session.add(kb)
    session.commit()
    session.refresh(kb)
    background.add_task(_advance_progress, kb_id)
    return kb


@router.get("/{kb_id}/documents")
def list_documents(kb_id: str, session: Session = Depends(get_session)) -> list[dict]:
    """原型没有文档列表页，先按知识库的 doc_count 生成占位文档，供详情页「查看文档」用。"""
    kb = session.get(models.KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail=f"知识库不存在: {kb_id}")
    samples = [
        ("产品需求文档 v2.1.pdf", "2.4 MB"),
        ("API 接入指南.md", "180 KB"),
        ("客户常见问题.docx", "640 KB"),
        ("部署运维手册.pdf", "3.1 MB"),
    ]
    return [
        {
            "id": f"{kb_id}-doc-{i + 1}",
            "name": name,
            "size": size,
            "chunks": 40 + i * 12,
            "status": "已入库" if kb.vector_progress >= 100 else "处理中",
        }
        for i, (name, size) in enumerate(samples)
    ]
