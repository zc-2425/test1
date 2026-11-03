"""数据库表模型。

约定：
1. 主键统一用**可读字符串**（`wf-001` / `agt-003`），方便前端 mock 与后端真数据无缝替换；
2. 状态字段直接存中文原值（`已发布` / `草稿` / `运行中`），颜色映射放在前端 StatusBadge，
   避免后端做视觉决策；
3. 字段命名对齐 docs/05-接口与数据模型草案.md，前端 DTO 可逐字段对应。
"""

from datetime import UTC, date, datetime

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    # SQLAlchemy 2.1 起拒绝 naive datetime，统一用带时区的 UTC
    return datetime.now(UTC).replace(microsecond=0)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(primary_key=True)
    username: str = Field(index=True, unique=True)
    display_name: str
    email: str
    role: str = "admin"
    avatar: str | None = None
    created_at: datetime = Field(default_factory=_now)


class Workflow(SQLModel, table=True):
    __tablename__ = "workflows"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    # 聊天流 / 工作流
    type: str = "工作流"
    # 已发布 / 草稿 / 运行中
    status: str = "草稿"
    node_count: int = 0
    success_rate: float = 0.0
    last_run_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Agent(SQLModel, table=True):
    __tablename__ = "agents"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    # 聊天助手 / 数据分析 / 内容创作 …
    type: str = "聊天助手"
    # Function Calling / ReAct / Chain of Thought
    strategy: str = "Function Calling"
    # 活跃 / 草稿 / 暂停 / 错误
    status: str = "活跃"
    avatar: str | None = None
    system_prompt: str = ""
    model_id: str | None = None
    tool_count: int = 0
    run_count: int = 0
    last_run_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class KnowledgeBase(SQLModel, table=True):
    __tablename__ = "knowledge_bases"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    doc_count: int = 0
    size_label: str = "0 MB"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 800
    chunk_overlap: int = 150
    # 已就绪 / 处理中 / 失败
    status: str = "已就绪"
    vector_progress: int = 100
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Dataset(SQLModel, table=True):
    """注意：数据集 ≠ 知识库。数据集是「解析 + 结构化记录」，知识库是「分块 + 向量化」，
    两者字段只有一个交集（name/description/status），不要合并表。"""

    __tablename__ = "datasets"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    # 文档 / 问答对 / 表格
    type: str = "文档"
    record_count: int = 0
    size_label: str = "0 MB"
    # 已完成 / 处理中 / 失败 / 待处理
    parse_status: str = "已完成"
    progress: int = 100
    created_at: datetime | None = None
    updated_at: datetime = Field(default_factory=_now)


class Prompt(SQLModel, table=True):
    __tablename__ = "prompts"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    category: str = "通用"
    model_id: str | None = None
    version: str = "v1"
    # 已发布 / 草稿
    status: str = "草稿"
    usage_count: int = 0
    content: str = ""
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Tool(SQLModel, table=True):
    __tablename__ = "tools"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    # 内置 / 自定义API
    type: str = "内置"
    # 列表页展示的自然语言版参数
    input_params: str = ""
    # 创建页填写的 schema 版参数（逗号分隔或 JSON），执行时用它
    input_schema: str = ""
    # 可用 / 停用
    status: str = "可用"
    call_count: int = 0
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class ModelProvider(SQLModel, table=True):
    __tablename__ = "model_providers"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    # 如 openai / anthropic / google / azure-openai / aws-bedrock / huggingface / ollama
    slug: str = Field(index=True, unique=True)
    model_count: int = 0
    # 已连接 / 未连接 / 错误 / 维护中 / 测试中
    status: str = "未连接"
    api_key_masked: str = ""
    enabled: bool = False
    base_url: str | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class App(SQLModel, table=True):
    __tablename__ = "apps"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    # 聊天机器人 / 智能体 / 工作流应用
    type: str = "聊天机器人"
    # 运行中 / 已停止 / 草稿
    status: str = "草稿"
    usage_count: int = 0
    agent_id: str | None = None
    workflow_id: str | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Plugin(SQLModel, table=True):
    __tablename__ = "plugins"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    category: str = "工具"
    author: str = "官方"
    rating: float = 0.0
    download_count: int = 0
    price: str = "免费"
    verified: bool = False
    installed: bool = False
    hot: bool = False


class Alert(SQLModel, table=True):
    """告警中心：概览页、成本页、告警弹窗三处必须同源，都查这张表。"""

    __tablename__ = "alerts"

    id: str = Field(primary_key=True)
    title: str
    detail: str = ""
    # 严重 / 警告 / 提示
    severity: str = "警告"
    # 未处理 / 已解决
    status: str = "未处理"
    source: str = "系统"
    created_at: datetime = Field(default_factory=_now)


class AbTest(SQLModel, table=True):
    __tablename__ = "ab_tests"

    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    model_a: str
    model_b: str
    # 运行中 / 已完成 / 已停止
    status: str = "运行中"
    sample_size: int = 0
    winner: str | None = None
    started_at: datetime = Field(default_factory=_now)


class Trace(SQLModel, table=True):
    """一次真实调用的埋点。LLMOps 的所有聚合都从这张表算出来。

    P1 起它由**真实调用**写入（对话流、工作流 LLM 节点），不再是种子数据。
    """

    __tablename__ = "traces"

    id: str = Field(primary_key=True)
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    status: str = "成功"
    # chat | prompt_test | workflow_run
    kind: str = Field(default="chat", index=True)
    # real | mock —— 供 LLMOps 区分真实消耗与模拟输出
    mode: str = Field(default="mock", index=True)
    # 失败时的错误摘要（成功为空）
    error: str | None = None

    # 归属：谁触发的这次调用
    conversation_id: str | None = Field(default=None, index=True)
    agent_id: str | None = Field(default=None, index=True)
    app_id: str | None = Field(default=None, index=True)
    workflow_id: str | None = Field(default=None, index=True)

    day: date = Field(default_factory=date.today, index=True)
    created_at: datetime = Field(default_factory=_now)


class Conversation(SQLModel, table=True):
    """一次完整会话（一次对话、一次提示词测试、一次工作流运行都算一次会话）。"""

    __tablename__ = "conversations"

    id: str = Field(primary_key=True)
    title: str = ""
    # prompt_test | workflow_run | app_chat
    source: str = Field(default="prompt_test", index=True)
    prompt_id: str | None = Field(default=None, index=True)
    agent_id: str | None = Field(default=None, index=True)
    app_id: str | None = Field(default=None, index=True)
    workflow_id: str | None = Field(default=None, index=True)

    message_count: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Message(SQLModel, table=True):
    """会话里的一条消息。assistant 消息带 token、耗时与模式，便于单条归因。"""

    __tablename__ = "messages"

    id: str = Field(primary_key=True)
    conversation_id: str = Field(index=True)
    # user | assistant | system
    role: str = "user"
    content: str = ""
    tokens: int = 0
    latency_ms: int = 0
    # real | mock
    mode: str = "mock"
    created_at: datetime = Field(default_factory=_now)
