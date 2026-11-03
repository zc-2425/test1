"""表结构增量补丁。

项目用 `create_all()` 建表，它只会**新建表**，不会给已有表加列。
所以新增字段时在这里登记一行 ALTER TABLE，启动时自动补齐 —— 练手阶段够用，
真项目应该上 Alembic（README 里也写明了这个取舍）。

只做**加列**，不做删改，避免误伤已有数据。
"""

from sqlalchemy import inspect, text

from app.db import engine

# (表名, 列名, 列定义)
_ADDITIONS: list[tuple[str, str, str]] = [
    ("traces", "kind", "VARCHAR DEFAULT 'chat'"),
    ("traces", "mode", "VARCHAR DEFAULT 'mock'"),
    ("traces", "error", "VARCHAR"),
    ("traces", "conversation_id", "VARCHAR"),
    ("traces", "agent_id", "VARCHAR"),
    ("traces", "app_id", "VARCHAR"),
    ("traces", "workflow_id", "VARCHAR"),
    ("knowledge_bases", "chunk_count", "INTEGER DEFAULT 0"),
    ("messages", "citations", "TEXT"),
]


def apply_schema_patches() -> list[str]:
    """返回本次实际新增的列，方便启动日志里看清楚做了什么。"""
    applied: list[str] = []
    inspector = inspect(engine)

    for table, column, ddl in _ADDITIONS:
        if table not in inspector.get_table_names():
            continue
        existing = {item["name"] for item in inspector.get_columns(table)}
        if column in existing:
            continue
        with engine.begin() as connection:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
        applied.append(f"{table}.{column}")

    return applied