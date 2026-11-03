"""RAG：切块 → 向量化 → 入库 → 检索。

存储用 SQLite：
- 文本在 `document_chunks`
- 向量在 `chunk_embeddings`（float32 BLOB，入库前 L2 归一化）

检索是**全量点积**（numpy），在本机实测 1 万块约 2ms、5 万块约 11ms。
到几十万块才需要换 ANN 索引（sqlite-vec / Chroma / pgvector）。
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

import numpy as np
from sqlmodel import Session, delete, select

from app import models
from app.services import embeddings as emb

# 中英混排都照顾：英文按单词、中文按单字 + bigram
_TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+|[\u4e00-\u9fa5]")


def tokenize(text: str) -> list[str]:
    """切 token：英文词 + 中文字/bigram。哈希向量与关键词打分都用它。"""
    raw = _TOKEN_RE.findall(text.lower())
    tokens = list(raw)
    # 中文 bigram：单字区分度太低
    chinese = [t for t in raw if len(t) == 1 and "\u4e00" <= t <= "\u9fa5"]
    tokens.extend(chinese[i] + chinese[i + 1] for i in range(len(chinese) - 1))
    return tokens


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, size: int = 800, overlap: int = 150) -> list[str]:
    """按段落/句末优先切开，带重叠，避免一句话被拦腰截断。"""
    text = normalize_text(text)
    if not text:
        return []
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            window = text[start:end]
            # 优先在段落处断，其次句末，最后换行
            for separator in ("\n\n", "。", "！", "？", "\n", "；"):
                cut = window.rfind(separator)
                if cut > size * 0.5:
                    end = start + cut + len(separator)
                    break
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    return chunks


def _doc_prefix(kb_id: str) -> str:
    return f"{kb_id}-doc"


def list_documents(session: Session, kb_id: str) -> list[models.KnowledgeDoc]:
    return list(
        session.exec(
            select(models.KnowledgeDoc)
            .where(models.KnowledgeDoc.kb_id == kb_id)
            .order_by(models.KnowledgeDoc.created_at.desc())
        ).all()
    )


def _drop_doc_index(session: Session, doc_id: str) -> None:
    chunk_ids = [
        row
        for row in session.exec(
            select(models.DocumentChunk.id).where(models.DocumentChunk.doc_id == doc_id)
        ).all()
    ]
    if chunk_ids:
        session.exec(delete(models.ChunkEmbedding).where(models.ChunkEmbedding.chunk_id.in_(chunk_ids)))
    session.exec(delete(models.DocumentChunk).where(models.DocumentChunk.doc_id == doc_id))
    session.commit()


def index_document(
    session: Session,
    kb: models.KnowledgeBase,
    doc: models.KnowledgeDoc,
    text: str,
) -> dict:
    """切块 + 向量化 + 入库。返回 {chunks, mode, model, ms}。"""
    import time

    started = time.perf_counter()
    doc.status = "处理中"
    doc.error = None
    session.add(doc)
    session.commit()

    try:
        pieces = chunk_text(text, size=kb.chunk_size or 800, overlap=kb.chunk_overlap or 150)
        if not pieces:
            raise ValueError("文档没有可用文本（可能全部是空白）")

        config = emb.resolve_config()
        vectors, mode = emb.embed_texts(pieces, config)

        _drop_doc_index(session, doc.id)

        now = datetime.now(UTC).replace(microsecond=0)
        for position, (piece, vector) in enumerate(zip(pieces, vectors, strict=True)):
            chunk = models.DocumentChunk(
                id=f"{doc.id}-c{position:04d}",
                kb_id=kb.id,
                doc_id=doc.id,
                position=position,
                content=piece,
                char_count=len(piece),
                created_at=now,
            )
            session.add(chunk)
            session.add(
                models.ChunkEmbedding(
                    chunk_id=chunk.id,
                    kb_id=kb.id,
                    model=config.model,
                    dim=int(vector.shape[0]),
                    vector=emb.to_bytes(vector),
                    created_at=now,
                )
            )

        # 把实际使用的向量模型写回知识库，避免详情页继续显示种子里的旧模型名
        kb.embedding_model = config.model

        doc.chunk_count = len(pieces)
        doc.char_count = len(text)
        doc.status = "已入库"
        doc.error = None
        session.add(doc)
        session.commit()

        # 知识库的统计跟着重算，列表页与详情页保持同源
        refresh_kb_stats(session, kb)

        return {
            "chunks": len(pieces),
            "mode": mode,
            "model": config.model,
            "ms": int((time.perf_counter() - started) * 1000),
        }
    except Exception as exc:  # noqa: BLE001 - 失败要写进文档状态，供界面展示
        session.rollback()
        doc.status = "失败"
        doc.error = str(exc)[:400]
        session.add(doc)
        session.commit()
        raise


def refresh_kb_stats(session: Session, kb: models.KnowledgeBase) -> models.KnowledgeBase:
    docs = list_documents(session, kb.id)
    kb.doc_count = len(docs)
    total_bytes = sum(doc.size_bytes for doc in docs)
    kb.size_label = (
        f"{total_bytes / 1024 / 1024:.1f} MB" if total_bytes >= 1024 * 1024 else f"{max(1, total_bytes // 1024)} KB"
    )
    indexed = [doc for doc in docs if doc.status == "已入库"]
    kb.vector_progress = 100 if docs and len(indexed) == len(docs) else (0 if not docs else int(len(indexed) / len(docs) * 100))
    kb.status = "已就绪" if kb.vector_progress >= 100 else ("处理中" if docs else "已就绪")
    kb.chunk_count = sum(doc.chunk_count for doc in docs)
    session.add(kb)
    session.commit()
    session.refresh(kb)
    return kb


def search(
    session: Session, kb: models.KnowledgeBase, query: str, top_k: int = 5
) -> dict:
    """检索：问题向量化 → 与该库所有分块做余弦 → 取 top_k。"""
    import time

    started = time.perf_counter()
    chunks = list(
        session.exec(
            select(models.DocumentChunk).where(models.DocumentChunk.kb_id == kb.id)
        ).all()
    )
    if not chunks:
        return {"query": query, "mode": "none", "tookMs": 0, "hits": [], "scanned": 0}

    rows = list(
        session.exec(
            select(models.ChunkEmbedding).where(models.ChunkEmbedding.kb_id == kb.id)
        ).all()
    )
    by_chunk = {row.chunk_id: row for row in rows}
    usable = [chunk for chunk in chunks if chunk.id in by_chunk]
    if not usable:
        return {"query": query, "mode": "none", "tookMs": 0, "hits": [], "scanned": 0}

    dim = by_chunk[usable[0].id].dim
    matrix = np.vstack([emb.from_bytes(by_chunk[chunk.id].vector, dim) for chunk in usable])

    config = emb.resolve_config()
    query_vectors, mode = emb.embed_texts([query], config)
    ranked = emb.cosine_top_k(query_vectors[0], matrix, top_k)

    docs = {doc.id: doc for doc in list_documents(session, kb.id)}
    hits = []
    for row_index, score in ranked:
        chunk = usable[row_index]
        doc = docs.get(chunk.doc_id)
        hits.append(
            {
                "chunkId": chunk.id,
                "docId": chunk.doc_id,
                "docName": doc.name if doc else "（文档已删除）",
                "position": chunk.position,
                "score": round(score, 4),
                "preview": chunk.content[:220],
            }
        )

    return {
        "query": query,
        "mode": mode,
        "model": config.model,
        "tookMs": int((time.perf_counter() - started) * 1000),
        "scanned": len(usable),
        "hits": hits,
    }
