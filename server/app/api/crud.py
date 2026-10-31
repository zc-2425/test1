"""通用 CRUD 路由器工厂。

9 个实体（工作流/Agent/知识库/数据集/提示词/工具/厂商/应用/插件）的分页、搜索、筛选、
详情、创建、局部更新、删除逻辑完全同构，抽在这里而不是复制 9 遍。

注 1：PATCH 用 `dict` 接收是有意的——只白名单写入模型真实字段，多余 key 直接丢弃，
      省掉 9 份 *Update 模型。
注 2：本文件**不能用** `from __future__ import annotations`。因为 `payload: create_model`
      引用的是闭包变量，只有注解在 def 执行时立即求值，FastAPI 才能拿到真实的类；
      一旦变成字符串延迟求值，get_type_hints 解析不到它。
"""

from typing import Any, Generic, TypeVar
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlmodel import Session, SQLModel, select

from app.db import get_session
from app.schemas import Page

ModelT = TypeVar("ModelT", bound=SQLModel)


class _Crud(Generic[ModelT]):
    def __init__(
        self,
        *,
        model: type[ModelT],
        out_model: type[Any],
        create_model: type[Any],
        prefix: str,
        tag: str,
        id_prefix: str,
        search_fields: tuple[str, ...] = ("name",),
        status_field: str = "status",
        type_field: str = "type",
        order_field: str = "created_at",
    ) -> None:
        self.model = model
        self.out_model = out_model
        self.create_model = create_model
        self.prefix = prefix
        self.tag = tag
        self.id_prefix = id_prefix
        self.search_fields = search_fields
        self.status_field = status_field
        self.type_field = type_field
        self.order_field = order_field

    # ---- 查询构造 ----
    def _stmt(self, keyword: str | None, status: str | None, type_: str | None):
        stmt = select(self.model)
        if keyword:
            conds = [
                getattr(self.model, f).contains(keyword)  # type: ignore[attr-defined]
                for f in self.search_fields
                if hasattr(self.model, f)
            ]
            if conds:
                stmt = stmt.where(or_(*conds))
        if status and hasattr(self.model, self.status_field):
            stmt = stmt.where(getattr(self.model, self.status_field) == status)
        if type_ and hasattr(self.model, self.type_field):
            stmt = stmt.where(getattr(self.model, self.type_field) == type_)
        return stmt

    def _order(self, stmt, sort: str | None, order: str | None):
        field_name = sort or self.order_field
        if not hasattr(self.model, field_name):
            field_name = "id"
        column = getattr(self.model, field_name)
        # created_at 可能为空（数据集允许空值），nullslast 避免空值排在最前面
        primary = column.asc().nullslast() if order == "asc" else column.desc().nullslast()
        # 同值时按 id 兜底，保证多次请求顺序稳定（否则分页会出现重复/漏行）
        return stmt.order_by(primary, getattr(self.model, "id").desc())

    def build(self) -> APIRouter:
        router = APIRouter(prefix=self.prefix, tags=[self.tag])
        model = self.model
        out_model = self.out_model
        create_model = self.create_model

        @router.get("", response_model=Page[out_model])  # type: ignore[valid-type]
        def list_items(  # noqa: ANN202
            page: int = Query(1, ge=1),
            size: int = Query(10, ge=1, le=200),
            q: str | None = Query(None, description="关键字，按名字等字段模糊匹配"),
            status: str | None = Query(None, description="状态精确匹配"),
            type: str | None = Query(None, description="类型精确匹配"),
            sort: str | None = Query(None, description="排序字段，默认按创建时间倒序"),
            order: str | None = Query(None, pattern="^(asc|desc)$", description="排序方向"),
            session: Session = Depends(get_session),
        ):
            stmt = self._stmt(q, status, type)
            total = session.exec(
                select(func.count()).select_from(stmt.subquery())  # type: ignore[arg-type]
            ).one()
            rows = session.exec(
                self._order(stmt, sort, order).offset((page - 1) * size).limit(size)
            ).all()
            return {"items": rows, "total": total, "page": page, "size": size}

        @router.get("/{item_id}", response_model=out_model)  # type: ignore[valid-type]
        def get_item(item_id: str, session: Session = Depends(get_session)):  # noqa: ANN202
            item = session.get(model, item_id)
            if item is None:
                raise HTTPException(status_code=404, detail=f"{self.tag} 不存在: {item_id}")
            return item

        # 注意：这里必须显式构造函数，让 `payload: create_model` 在 def 执行时求值成真实类，
        # FastAPI 才能拿到类型（所以本文件禁用 `from __future__ import annotations` 的懒求值）
        def _create(payload, session: Session):  # noqa: ANN001, ANN202
            data = payload.model_dump(exclude_unset=True)
            data.setdefault("id", f"{self.id_prefix}-{uuid4().hex[:8]}")
            item = model(**data)
            session.add(item)
            session.commit()
            session.refresh(item)
            return item

        @router.post("", response_model=out_model, status_code=201)  # type: ignore[valid-type]
        def create_item(  # noqa: ANN202
            payload: create_model,  # type: ignore[valid-type]
            session: Session = Depends(get_session),
        ):
            return _create(payload, session)

        @router.patch("/{item_id}", response_model=out_model)  # type: ignore[valid-type]
        def update_item(  # noqa: ANN202
            item_id: str,
            payload: dict[str, Any] = Body(...),
            session: Session = Depends(get_session),
        ):
            item = session.get(model, item_id)
            if item is None:
                raise HTTPException(status_code=404, detail=f"{self.tag} 不存在: {item_id}")
            allowed = set(model.model_fields) - {"id"}
            for key, value in payload.items():
                if key in allowed:
                    setattr(item, key, value)
            session.add(item)
            session.commit()
            session.refresh(item)
            return item

        @router.delete("/{item_id}", status_code=204)
        def delete_item(item_id: str, session: Session = Depends(get_session)) -> None:
            item = session.get(model, item_id)
            if item is None:
                raise HTTPException(status_code=404, detail=f"{self.tag} 不存在: {item_id}")
            session.delete(item)
            session.commit()

        return router
