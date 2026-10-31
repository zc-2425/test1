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

    # P12 才会用到；留空表示走 mock 实现
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings
