"""9 个核心实体的 CRUD 路由，全部由通用工厂生成。

路径与 docs/05 §4 的接口清单一致：
    GET/POST     /api/workflows
    GET/PATCH/DELETE /api/workflows/{id}
"""

from fastapi import APIRouter

from app.api.crud import _Crud
from app.models import (
    Agent,
    App,
    Dataset,
    KnowledgeBase,
    ModelProvider,
    Plugin,
    Prompt,
    Tool,
    Workflow,
)
from app.schemas import (
    AgentCreate,
    AppCreate,
    DatasetCreate,
    KnowledgeBaseCreate,
    PluginCreate,
    PromptCreate,
    ProviderCreate,
    ToolCreate,
    WorkflowCreate,
)

router = APIRouter()

router.include_router(
    _Crud(
        model=Workflow,
        out_model=Workflow,
        create_model=WorkflowCreate,
        prefix="/workflows",
        tag="工作流",
        id_prefix="wf",
        search_fields=("name", "description"),
    ).build()
)

router.include_router(
    _Crud(
        model=Agent,
        out_model=Agent,
        create_model=AgentCreate,
        prefix="/agents",
        tag="Agent",
        id_prefix="agt",
        search_fields=("name", "description"),
    ).build()
)

router.include_router(
    _Crud(
        model=KnowledgeBase,
        out_model=KnowledgeBase,
        create_model=KnowledgeBaseCreate,
        prefix="/knowledge-bases",
        tag="知识库",
        id_prefix="kb",
        search_fields=("name", "description"),
    ).build()
)

router.include_router(
    _Crud(
        model=Dataset,
        out_model=Dataset,
        create_model=DatasetCreate,
        prefix="/datasets",
        tag="数据集",
        id_prefix="ds",
        search_fields=("name", "description"),
        status_field="parse_status",
    ).build()
)

router.include_router(
    _Crud(
        model=Prompt,
        out_model=Prompt,
        create_model=PromptCreate,
        prefix="/prompts",
        tag="提示词",
        id_prefix="pmt",
        search_fields=("name", "description"),
        type_field="category",
    ).build()
)

router.include_router(
    _Crud(
        model=Tool,
        out_model=Tool,
        create_model=ToolCreate,
        prefix="/tools",
        tag="工具",
        id_prefix="tool",
        search_fields=("name", "description"),
    ).build()
)

router.include_router(
    _Crud(
        model=ModelProvider,
        out_model=ModelProvider,
        create_model=ProviderCreate,
        prefix="/providers",
        tag="模型厂商",
        id_prefix="prov",
        search_fields=("name", "slug"),
        type_field="slug",
    ).build()
)

router.include_router(
    _Crud(
        model=App,
        out_model=App,
        create_model=AppCreate,
        prefix="/apps",
        tag="应用中心",
        id_prefix="app",
        search_fields=("name", "description"),
    ).build()
)

router.include_router(
    _Crud(
        model=Plugin,
        out_model=Plugin,
        create_model=PluginCreate,
        prefix="/plugins",
        tag="插件市场",
        id_prefix="plug",
        search_fields=("name", "description"),
        status_field="category",
        type_field="category",
        order_field="download_count",
    ).build()
)
