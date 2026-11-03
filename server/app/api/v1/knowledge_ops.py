"""知识库：真实上传 → 切块 → embedding → 入库 → 检索。

P2 之前这里的文档是按 doc_count 编出来的占位数据；现在读写的是
`knowledge_docs` / `document_chunks` / `chunk_embeddings` 三张表。

支持格式：txt / md / csv / json / log（按文本读），pdf 需要可选的 pypdf。
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app import models
from app.core.config import get_settings
from app.db import engine, get_session
from app.services import embeddings as emb
from app.services import rag

router = APIRouter(prefix="/knowledge-bases", tags=["知识库"])

TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".csv", ".json", ".log", ".yml", ".yaml"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


class SearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


def _human_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} MB"
    return f"{max(1, round(size / 1024))} KB"


def _read_text(raw: bytes, suffix: str, name: str) -> str:
    if suffix in TEXT_SUFFIXES:
        for encoding in ("utf-8", "utf-8-sig", "gbk"):
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise HTTPException(status_code=415, detail=f"「{name}」无法按 UTF-8/GBK 解码")

    if suffix == ".pdf":
        try:
            import pypdf  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - 取决于是否装了可选依赖
            raise HTTPException(
                status_code=415,
                detail="PDF 需要可选依赖：uv pip install pypdf --python .venv\\Scripts\\python.exe",
            ) from exc
        reader = pypdf.PdfReader(io.BytesIO(raw))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)

    raise HTTPException(
        status_code=415,
        detail=f"暂不支持 {suffix or '无扩展名'} 格式（支持 txt/md/csv/json/log，PDF 需装 pypdf）",
    )


@router.get("/embeddings/status")
def embedding_status() -> dict:
    """当前用的是真 embedding 还是本地哈希向量。"""
    return emb.health()


@router.get("/{kb_id}/documents")
def list_documents(kb_id: str, session: Session = Depends(get_session)) -> list[dict]:
    kb = session.get(models.KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail=f"知识库不存在: {kb_id}")
    return [
        {
            "id": doc.id,
            "name": doc.name,
            "fileType": doc.file_type,
            "size": _human_size(doc.size_bytes),
            "sizeBytes": doc.size_bytes,
            "charCount": doc.char_count,
            "chunks": doc.chunk_count,
            "status": doc.status,
            "error": doc.error,
            "createdAt": doc.created_at,
        }
        for doc in rag.list_documents(session, kb_id)
    ]


@router.post("/{kb_id}/documents", status_code=201)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> dict:
    kb = session.get(models.KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail=f"知识库不存在: {kb_id}")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="文件是空的")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="文件超过 20MB")

    name = Path(file.filename or "未命名.txt").name
    suffix = Path(name).suffix.lower()
    text = _read_text(raw, suffix, name)
    if not text.strip():
        raise HTTPException(status_code=400, detail="解析后没有文本内容（可能是扫描版 PDF）")

    # 原始文件留档，便于排查解析问题，也供「重建索引」复用
    upload_dir = Path(get_settings().upload_dir) / kb_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / name).write_bytes(raw)

    doc = models.KnowledgeDoc(
        id=f"kdoc-{uuid4().hex[:8]}",
        kb_id=kb_id,
        name=name,
        file_type=suffix.lstrip(".") or "txt",
        size_bytes=len(raw),
        char_count=len(text),
        created_at=datetime.now(UTC).replace(microsecond=0),
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    try:
        result = rag.index_document(session, kb, doc, text)
    except Exception as exc:  # noqa: BLE001 - 索引失败要把原因带回前端
        raise HTTPException(status_code=500, detail=f"索引失败：{exc}") from exc

    session.refresh(doc)
    return {
        "id": doc.id,
        "name": doc.name,
        "chunks": doc.chunk_count,
        "status": doc.status,
        "mode": result["mode"],
        "model": result["model"],
        "tookMs": result["ms"],
    }


@router.delete("/{kb_id}/documents/{doc_id}", status_code=204)
def delete_document(kb_id: str, doc_id: str, session: Session = Depends(get_session)) -> None:
    doc = session.get(models.KnowledgeDoc, doc_id)
    if doc is None or doc.kb_id != kb_id:
        raise HTTPException(status_code=404, detail=f"文档不存在: {doc_id}")
    kb = session.get(models.KnowledgeBase, kb_id)
    rag._drop_doc_index(session, doc_id)
    session.delete(doc)
    session.commit()
    if kb is not None:
        rag.refresh_kb_stats(session, kb)


@router.get("/{kb_id}/documents/{doc_id}/chunks")
def list_chunks(
    kb_id: str,
    doc_id: str,
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> dict:
    doc = session.get(models.KnowledgeDoc, doc_id)
    if doc is None or doc.kb_id != kb_id:
        raise HTTPException(status_code=404, detail=f"文档不存在: {doc_id}")

    chunks = list(
        session.exec(
            select(models.DocumentChunk)
            .where(models.DocumentChunk.doc_id == doc_id)
            .order_by(models.DocumentChunk.position)
            .limit(limit)
        ).all()
    )
    return {
        "docId": doc_id,
        "docName": doc.name,
        "total": doc.chunk_count,
        "chunks": [
            {
                "id": chunk.id,
                "position": chunk.position,
                "chars": chunk.char_count,
                "content": chunk.content,
            }
            for chunk in chunks
        ],
    }


@router.post("/{kb_id}/search")
def search(kb_id: str, payload: SearchIn, session: Session = Depends(get_session)) -> dict:
    """检索测试：问题 → 向量 → 余弦 top_k。界面上要能看到分数与来源。"""
    kb = session.get(models.KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail=f"知识库不存在: {kb_id}")
    return rag.search(session, kb, payload.query, payload.top_k)


@router.post("/{kb_id}/reindex")
def reindex(
    kb_id: str,
    background: BackgroundTasks,
    session: Session = Depends(get_session),
) -> models.KnowledgeBase:
    """重建索引：按文档逐个重切块并重新向量化（真干活，不再只是推进度条）。"""
    kb = session.get(models.KnowledgeBase, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail=f"知识库不存在: {kb_id}")

    docs = rag.list_documents(session, kb_id)
    kb.status = "处理中"
    kb.vector_progress = 0
    session.add(kb)
    session.commit()
    session.refresh(kb)

    if docs:
        background.add_task(_reindex_all, kb_id)
    else:
        kb.status = "已就绪"
        kb.vector_progress = 100
        session.add(kb)
        session.commit()
        session.refresh(kb)
    return kb


def _reindex_all(kb_id: str) -> None:
    """后台任务：重新索引该库所有文档，进度按文档数推进。"""
    upload_dir = Path(get_settings().upload_dir) / kb_id
    with Session(engine) as session:
        kb = session.get(models.KnowledgeBase, kb_id)
        if kb is None:
            return
        docs = rag.list_documents(session, kb_id)
        total = len(docs) or 1
        for index, doc in enumerate(docs, start=1):
            path = upload_dir / doc.name
            try:
                if not path.exists():
                    raise FileNotFoundError(f"原始文件已丢失：{doc.name}")
                text = _read_text(path.read_bytes(), f".{doc.file_type}", doc.name)
                rag.index_document(session, kb, doc, text)
            except Exception as exc:  # noqa: BLE001 - 单个文档失败不影响其它
                session.rollback()
                doc.status = "失败"
                doc.error = str(exc)[:400]
                session.add(doc)
                session.commit()
            kb.vector_progress = int(index / total * 100)
            session.add(kb)
            session.commit()
