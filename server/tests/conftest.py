"""测试夹具：必须在导入 app 之前改掉数据库路径，避免污染开发库。

临时库固定落在 `server/.pytest_tmp/`，不使用 `tempfile.mkdtemp()`——
本机的 TMP 环境变量曾被重定向到工作目录，导致临时库散落在仓库里。
"""

import os
import shutil
from pathlib import Path

_TMP_ROOT = Path(__file__).resolve().parents[1] / ".pytest_tmp"
if _TMP_ROOT.exists():
    shutil.rmtree(_TMP_ROOT, ignore_errors=True)
_TMP_ROOT.mkdir(parents=True, exist_ok=True)

os.environ["APP_DB_PATH"] = str(_TMP_ROOT / "test.db")
os.environ["APP_UPLOAD_DIR"] = str(_TMP_ROOT / "uploads")
os.environ["APP_SEED_ON_STARTUP"] = "true"
# 测试固定走模拟实现：不受本机 APP_DEEPSEEK_API_KEY 之类的影响
os.environ["APP_LLM_MODE"] = "mock"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    # with 语法会触发 lifespan：建表 + 灌种子
    with TestClient(app) as test_client:
        yield test_client