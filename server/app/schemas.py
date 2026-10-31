"""请求/响应模型。

统一响应信封（对齐 docs/05 §5 的分页约定）：
    { "items": [...], "total": 42, "page": 1, "size": 10 }

创建请求用独立的 *Create 模型，不直接复用表模型，
这样客户端传上来的多余字段（比如自己编的 id）不会污染数据。
"""

from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlmodel import SQLModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int


class HealthOut(BaseModel):
    status: str
    app: str
    version: str
    db: str
    seed_ready: bool


class LoginIn(BaseModel):
    username: str
    password: str


class LoginOut(BaseModel):
    token: str
    user: dict


# ---------------- 创建请求 ----------------
class WorkflowCreate(SQLModel):
    name: str
    description: str = ""
    type: str = "工作流"
    status: str = "草稿"
    node_count: int = 0


class AgentCreate(SQLModel):
    name: str
    description: str = ""
    type: str = "聊天助手"
    strategy: str = "Function Calling"
    status: str = "草稿"
    system_prompt: str = ""
    tool_count: int = 0


class KnowledgeBaseCreate(SQLModel):
    name: str
    description: str = ""
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 800
    chunk_overlap: int = 150
    status: str = "处理中"


class DatasetCreate(SQLModel):
    name: str
    description: str = ""
    type: str = "文档"
    parse_status: str = "待处理"


class PromptCreate(SQLModel):
    name: str
    description: str = ""
    category: str = "通用"
    content: str = ""
    status: str = "草稿"


class ToolCreate(SQLModel):
    name: str
    description: str = ""
    type: str = "内置"
    input_params: str = ""
    input_schema: str = ""
    status: str = "可用"


class ProviderCreate(SQLModel):
    name: str
    slug: str
    base_url: str | None = None
    api_key_masked: str = ""
    enabled: bool = False


class AppCreate(SQLModel):
    name: str
    description: str = ""
    type: str = "聊天机器人"
    status: str = "草稿"
    agent_id: str | None = None
    workflow_id: str | None = None


class PluginCreate(SQLModel):
    name: str
    description: str = ""
    category: str = "工具"
    author: str = "官方"
    price: str = "免费"
    verified: bool = False
