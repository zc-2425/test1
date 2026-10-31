"""FastAPI 应用入口。

启动流程：建表 → 库为空则灌种子数据 → 挂载路由。
本地开发：uvicorn app.main:app --reload --port 5274
接口文档：http://127.0.0.1:5274/docs
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.api.v1 import auth, knowledge_ops, llmops, resources, system, workflow_ops
from app.core.config import get_settings
from app.db import create_db_and_tables, engine
from app.seed import seed_if_empty

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    if settings.seed_on_startup:
        with Session(engine) as session:
            seeded = seed_if_empty(session)
        if seeded:
            print("[seed] 已灌入初始数据")
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="通用 AI 智能体应用开发平台 —— 本地练手后端（SQLite + 同步 SQLModel）",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix=settings.api_prefix)
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(resources.router)
api_router.include_router(llmops.router)
api_router.include_router(knowledge_ops.router)
api_router.include_router(workflow_ops.router)

app.include_router(api_router)


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "api": settings.api_prefix,
        "health": f"{settings.api_prefix}/health",
    }
