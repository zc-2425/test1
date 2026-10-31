"""数据库：同步 SQLModel + SQLite。

选同步而非异步的理由：
1. 本地单用户练手，QPS 极低，同步 Session 完全够用；
2. 同步链路不需要 greenlet / aiosqlite，在 Python 3.14 这种新版本上少一个踩坑点；
3. FastAPI 会把 `def` 端点丢进线程池，不会阻塞事件循环。
"""

from collections.abc import Iterator

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

_settings = get_settings()

engine: Engine = create_engine(
    _settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    # 引入 models 让 SQLModel 完成表注册
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
