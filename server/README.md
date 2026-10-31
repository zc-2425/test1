# 后端（FastAPI + SQLite）

本地练手用后端，不做部署。**依赖全部装在 `server/.venv`，不碰 Anaconda 全局环境。**

## 起步

```bash
cd server

# 首次：创建虚拟环境并安装（uv 比 pip 快很多；没有 uv 就把 uv pip 换成 pip）
uv venv .venv --python 3.14
uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt

# 起服务（自动建表 + 首次灌种子数据）
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 5274
```

- 接口文档：http://127.0.0.1:5274/docs
- 健康检查：http://127.0.0.1:5274/api/health
- 前端端口 5273 已配 `/api` → 5274 的代理，前端代码只写 `/api/...`

也可以在仓库根目录用脚本（pnpm 转发）：

```bash
pnpm dev:server     # 起后端
pnpm test:server    # 跑冒烟测试
```

## 目录

```
server/
├─ app/
│  ├─ main.py              FastAPI 入口：建表 → 灌种子 → 挂路由 → CORS
│  ├─ core/config.py       pydantic-settings，全部走 APP_ 前缀环境变量 / .env
│  ├─ db.py                同步 SQLModel + SQLite（不引 greenlet/aiosqlite）
│  ├─ models.py            13 张表
│  ├─ schemas.py           Page[T] 分页信封 + 各实体 *Create 模型
│  ├─ seed.py              种子数据（名字与数字照抄截图）
│  └─ api/
│     ├─ crud.py           通用 CRUD 路由器工厂（分页/搜索/筛选/详情/改/删）
│     └─ v1/
│        ├─ resources.py   9 个实体挂上工厂
│        ├─ system.py      /health、/meta/overview、/alerts
│        ├─ auth.py        登录（练手版 token，非 JWT）
│        ├─ llmops.py      概览 / 成本序列 / 模型性能 / AB 测试
│        ├─ knowledge_ops.py  重建索引（进度真会动）、文档列表
│        └─ workflow_ops.py   运行工作流（确定性 trace）、发布
├─ tests/                  pytest 冒烟测试（11 个，用临时库，不污染 data/app.db）
├─ data/app.db             SQLite 文件（gitignore）
└─ uploads/                上传目录（gitignore）
```

## 几个刻意的选择

| 选择 | 理由 |
|---|---|
| **同步** SQLModel 而不是 async | 单用户本地、QPS 极低；同步链路不需要 greenlet/aiosqlite，在 Python 3.14 上少一个踩坑点。FastAPI 会把 `def` 端点丢线程池，不阻塞事件循环 |
| 主键用**可读字符串**（`wf-001`） | 前端的 mock id 与后端真数据同构，切换时不用改前端 |
| 状态字段存**中文原值** | 颜色映射属于视觉决策，放前端的 `StatusBadge`，后端不掺和 |
| PATCH 收 `dict` 后白名单过滤 | 省掉 9 份 `*Update` 模型；创建入口仍有 Pydantic 校验 |
| 时间统一 **UTC 时区感知** | SQLAlchemy 2.1 起拒绝 naive datetime，这条约束值得遵守 |
| 成本/成功率全部**聚合算出** | 原型有「同一指标两处不同值」的 bug（71.2% vs 78%），根因是写死了两份 |

## 已知取舍

- 没上 Alembic 迁移：练手阶段直接 `create_all`。表结构要改了就先删 `data/app.db` 重启。
- 登录是假 token（`dev-admin`），没做 JWT/密码哈希。接口形状与真实方案一致，换实现不影响前端。
- 上传接口只落了目录占位，真正的解析/向量化是模拟进度，不是真跑 embedding。
- 多进程部署会因 SQLite 单写锁出问题——本项目不考虑部署。
