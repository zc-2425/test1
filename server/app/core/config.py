"""应用配置：全部来自环境变量或 server/.env，不读系统级配置。"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=SERVER_DIR / ".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )

    app_name: str = "AI 智能体应用开发平台 API"
    api_prefix: str = "/api"
    debug: bool = True

    # SQLite 落在 server/data 下，随项目走，不污染系统
    db_path: Path = SERVER_DIR / "data" / "app.db"

    # 上传目录（知识库 / 数据集文档）
    upload_dir: Path = SERVER_DIR / "uploads"

    # 启动时若库为空则灌入种子数据
    seed_on_startup: bool = True

    # 允许的前端来源
    cors_origins: list[str] = [
        "http://127.0.0.1:5273",
        "http://localhost:5273",
        "http://127.0.0.1:4173",
    ]

    # ===== LLM 调用 =====
    # auto：有 Key 走真调用，没 Key 回落 mock；real：强制真调用（没 Key 直接报错）；mock：强制模拟
    llm_mode: str = "auto"
    llm_default_provider: str = "deepseek"
    llm_default_model: str = "deepseek-chat"
    llm_timeout: float = 60.0

    # Key 只从环境变量 / .env 读，绝不落库（库里只存掩码）
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    # 硅基流动：chat 与 embedding 共用一个 Key；不单独填则自动回落用 embedding 的 Key
    siliconflow_api_key: str | None = None
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    # ===== RAG / Embedding =====
    # auto：有 Key 走真 embedding，没 Key 用本地哈希向量（离线也能检索）；real / mock 可强制
    embedding_mode: str = "auto"
    embedding_provider: str = "siliconflow"
    embedding_base_url: str = "https://api.siliconflow.cn/v1"
    embedding_model: str = "BAAI/bge-m3"
    embedding_api_key: str | None = None
    embedding_dim: int = 1024
    # 一次请求最多送多少条文本（硅基流动限制较宽松，32 稳妥）
    embedding_batch: int = 32
    embedding_timeout: float = 60.0

    # 本地 Ollama 不需要 Key
    ollama_base_url: str = "http://127.0.0.1:11434/v1"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings
