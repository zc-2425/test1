# AI 智能体应用开发平台 · 高保真复刻

一个从 0 到 1 的练手项目：把墨刀原型 [通用-AI智能体应用开发平台（60P+）](https://modao.cc/com24/details/mtmdet7sycn18vyr) 复刻成可运行的全栈应用。不做部署：前端 + 本地 FastAPI + SQLite，真调用大模型做成可插拔模块。

## 技术栈

| 层 | 选型 | 理由 |
|---|---|---|
| 前端框架 | Vue 3.5 + TypeScript 5.9 | |
| 构建 | Vite 7.3 | |
| UI | Vuetify 3.13 | 设计稿是 M3 风格（主色 `#6750A4` 正好是 M3 baseline primary），Vuetify 的 M3 组件吻合度最高 |
| 路由 | Vue Router 4.6 | |
| 状态 | Pinia 3.0 | |
| 图标 | `@mdi/font` | 与 M3 图标同族 |
| 图表 | ECharts 6（按需引入） | LLMOps 的折线/柱状/堆叠图；只注册 line/bar/pie + 必要组件，单独懒加载 chunk 约 95KB gzip |
| 后端 | FastAPI 0.162 + SQLModel + SQLite | 同步链路，不引 greenlet/aiosqlite；真实 AI 生态（LangChain/向量库）在 Python 侧 |
| 后端隔离 | `server/.venv`（uv 创建） | 不碰 Anaconda 全局 site-packages |
| LLM 调用 | OpenAI 兼容协议（DeepSeek / OpenAI / Ollama） | 一个 httpx 流式客户端通吃；没配 Key 时自动回落本地模拟，并在界面上如实标注 |

> 前端依赖都锁在「已知稳定的大版本线」上，没有跟进 Vite 8 / TS 7 / ESLint 10 / Vuetify 4 这些新大版本。

## 起步

```bash
pnpm install
pnpm dev            # 前端 http://127.0.0.1:5273
pnpm dev:server     # 后端 http://127.0.0.1:5274/docs（另开一个终端）

pnpm typecheck      # vue-tsc 全量类型检查
pnpm lint           # eslint 扁平配置
pnpm build          # 类型检查 + 产出 dist/
pnpm test:server    # 后端 pytest 冒烟测试

# 开发期工具：走 Edge 的 CDP 打开页面 → 可先执行一段 JS（点按钮）→ 截图
# 用来验证 toast / 弹窗 / 抽屉这类「点了才出现」的交互态
node scripts/dev-screenshot.mjs --url http://127.0.0.1:5273/dev/ui --out _ref/_shots/kit.png
```

前端只写 `/api/...`，由 Vite 代理到 5274（见 `vite.config.ts`），所以浏览器里不存在跨域。

环境要求：Node ≥ 20.19（当前 v24.19）、Python 3.14（Anaconda）+ 项目内 venv。项目自带 `.npmrc`（npmmirror 源）与 `pnpm-workspace.yaml`（放行 esbuild 的安装脚本），只作用于本目录。

## 目录约定

```
src/                      前端
├─ app/
│  ├─ layouts/         AppShell / ShellTopbar / ShellSidebar（布局壳）
│  └─ router/          routes.ts（31 条路由 + meta 规格）/ nav.ts（侧栏 11 项）/ skeletons.ts
├─ views/              页面，一个路由一个文件，按模块建子目录
│  ├─ auth/            LoginView
│  ├─ stubs/           StubView（占位页 = 规格浏览器，逐页替换）
│  ├─ explore/ workflow/ app/ knowledge/ agent/
│  └─ prompt/ llmops/ plugin/ dataset/ tool/ providers/
├─ components/         跨页通用组件（P3/P4 建）
├─ features/           域内复杂组件（画布/对话/图表，P9/P10 建）
├─ styles/             tokens.css（设计令牌）/ base.css（重置+工具类）
├─ composables/        useToast（命令式提示）/ useConfirm（Promise 化确认）
├─ plugins/            vuetify.ts（主题）
├─ api/                接口层唯一出口：http.ts（fetch 封装）/ resources.ts（9 实体工厂）/ types.ts（DTO）
├─ mock/               假数据（P5 起逐步加）
├─ stores/             Pinia
└─ types/              router.d.ts / common.ts 等类型声明

scripts/                  开发工具（CDP 截图脚本）

server/                   后端（详见 server/README.md）
├─ app/
│  ├─ main.py          入口：建表 → 灌种子 → 挂路由 → CORS
│  ├─ models.py        13 张表
│  ├─ schemas.py       Page[T] 分页信封 + 各实体 *Create
│  ├─ seed.py          种子数据（名字与数字照抄截图）
│  └─ api/
│     ├─ crud.py       通用 CRUD 工厂（分页/搜索/筛选/详情/改/删）
│     └─ v1/           resources · system · auth · llmops · knowledge_ops · workflow_ops
└─ tests/              pytest 冒烟（临时库，不污染 data/app.db）
```

### 几条硬约定

1. **设计令牌只在 `src/styles/tokens.css` 里改**，组件内不写死颜色/圆角/尺寸。
2. **侧栏高亮按 `route.meta.navKey` 判定**，不按菜单文案——原型有 2 处高亮错位，这里已纠正。
3. **路由 meta 带规格**：`title / subtitle / module / navKey / skeleton / phase / screen / todo`。占位页会把它渲染成一张「规格卡」，实现完一页就把 `todo` 清空。
4. **原型自身的 bug 不照抄**：表头错位、状态跨页矛盾、画布无边线、字段英文、`API 密钥` 被截断等，详见 `docs/01-页面清单.md` 末节。
5. **知识库 ≠ 数据集**，是两个独立实体，不能共用 store 或表结构（后端是 `knowledge_bases` 与 `datasets` 两张表）。
6. **状态字段存中文原值**，颜色映射只在前端 `StatusBadge` 做，后端不做视觉决策。

## 阶段进度

| 阶段 | 内容 | 状态 |
|---|---|---|
| P0 | 工程基建（Vite + TS + ESLint + Prettier + 目录） | ✅ |
| P1 | 布局骨架 + 31 条路由占位 + 占位页规格卡 | ✅ |
| P2 | 设计令牌 + Vuetify 主题 + 字体/图标 | ✅ |
| P3 | 基础组件 A（骨架 / 数据展示）：10 个组件 + `/dev/ui` 组件预览页 | ✅ |
| P4 | 基础组件 B（表单 / 反馈 12 件 + 4 个页面级配方） | ✅ |
| **P4.5** | **FastAPI + SQLite 后端：13 表 / 9 实体 CRUD / 种子数据 / 冒烟测试** | **✅** |
| P5 | 列表页族（7 页）：真接口分页 / 搜索 / 筛选 / 排序 / 行内操作 / 删除确认 | ✅ |
| P6 | 详情页族（5 实体详情 + 提供商列表/详情，含 3 个原型未画的 Tab） | ✅ |
| P7 | 创建页族：知识库/Agent/工具创建 + 8 个配置模板 + 工作流模板页与创建弹窗 | ✅ |
| P8 | 探索（模板广场，16 个模板 + 收藏）+ 插件市场（12 个插件，安装真写库） | ✅ |
| P9 | 编辑器族：提示词编辑器（流式测试）+ 自研工作流画布（拖拽/连线/缩放/属性面板） | ✅ |
| P10 | LLMOps 五 Tab（ECharts 图表 + 真数据聚合）+ 告警/设置弹窗 | ✅ |
| P11 | 登录真实化（邮箱登录 + 校验 + 错误态）+ 路由守卫 + 会话持久化 | ✅ |
| P12 | 真调用可插拔：真 SSE 对话 / 工作流 LLM 节点真调用 / 厂商连通性真测试 | ✅ |

## 产品化改造（P1 起，让演示变真）

之前 12 个阶段把 62 张画布的「形」做完了；从 P1 开始补「真实的数据流」。
LLMOps 的指标现在**不再有种子数据**——首次打开是全 0，跑一次对话才会出现数字。

| 编号 | 内容 | 状态 |
|---|---|---|
| P1 | **会话持久化 + 真实 trace 写入**：conversations / messages 两张新表，每次调用写 1 条会话 + N 条消息 + 1 条 trace；LLMOps 全部聚合改读真实数据；提示词编辑器加「历史」抽屉；Agent 运行历史接真实查询 | ✅ |
| P2 | RAG 真链路（解析 → 分块 → embedding → 检索 → 引用） | ⬜ |
| P3 | 评测集 + 回归（把「感觉不错」变成「数据说不错」） | ⬜ |
| P4 | 工作流执行引擎 + 节点配置持久化 | ⬜ |
| P5 | 工具执行沙箱 + 调用审计 | ⬜ |
| P6 | 多租户 + RBAC + 审计日志 | ⬜ |

> 表结构用 `server/app/migrate.py` 做**加列**补丁（启动时自动执行），没有引 Alembic。
> 已上线的旧库不会被删表，只会补列。

## 设计文档

| 文档 | 说明 |
|---|---|
| [01-页面清单](docs/01-页面清单.md) | 62 画布 → 31 路由 + 2 弹窗态，含去重与原型缺陷清单 |
| [02-信息架构](docs/02-信息架构.md) | 侧栏菜单树、路由高亮映射、页面族、跳转图、浮层层级 |
| [03-组件与模式清单](docs/03-组件与模式清单.md) | 36 个组件、28 个状态值配色、8 种骨架配方、33 条路由归属 |
| [04-设计令牌](docs/04-设计令牌.md) | 11 组令牌（标注实测/推算）、`:root`、Vuetify 主题、M3 判定 |
| [05-接口与数据模型草案](docs/05-接口与数据模型草案.md) | 24 实体、96 条接口、24 份 Mock JSON、SSE 约定、Pinia 划分 |
| [_ref/recording-walkthrough.md](_ref/recording-walkthrough.md) | 85 秒录屏逐秒还原 |

`_ref/` 下是原始素材：62 张截图、逐秒抽帧，以及 `_spec/` 里 62 页的逐张规格 JSON。抽帧与规格 JSON 已在 `.gitignore` 中排除。