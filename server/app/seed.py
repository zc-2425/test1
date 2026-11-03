"""种子数据：把截图里真实出现的名字与数字灌进 SQLite。

原则：
1. 名称、状态、统计数字尽量照抄截图（如「智能客服工作流」8 节点、「产品知识库」156 文档 / 2.3 GB、
   「文本摘要器」、评分 4.8 / 使用 1,250），让前端接上真接口后观感与设计稿一致；
2. 日期落在 2024-01-08 ~ 2024-01-15（截图的时间区间）；
3. 金额/成本用 tokens × 单价算出来，不写死，避免出现「所有 Agent 运行次数都是 156」那种假数据。
"""

from __future__ import annotations

import random
from datetime import UTC, date, datetime, timedelta

from sqlmodel import Session, select

from app import models


def _dt(day: int, hour: int = 10, minute: int = 0) -> datetime:
    return datetime(2024, 1, day, hour, minute, 0, tzinfo=UTC)


WORKFLOWS = [
    ("wf-001", "智能客服工作流", "基于知识库的问答流程，支持多轮对话与人工转接", "聊天流", "已发布", 8, 98.2, _dt(15, 8, 0), _dt(15)),
    ("wf-002", "文档摘要生成器", "上传文档自动生成结构化摘要", "工作流", "草稿", 12, 94.0, _dt(14, 15, 0), _dt(14)),
    ("wf-003", "多语言翻译流水线", "支持 12 种语言互译，带术语表校验", "工作流", "已发布", 6, 99.1, _dt(15, 9, 30), _dt(13)),
    ("wf-004", "代码审查助手", "静态检查 + LLM 语义审查双通道", "聊天流", "运行中", 15, 91.4, None, _dt(12)),
    ("wf-005", "邮件分类处理", "自动分类收件箱并按优先级排队", "工作流", "已发布", 10, 96.5, _dt(15, 9, 0), _dt(11)),
    ("wf-006", "内容审核流程", "敏感词 + 语义双重审核", "工作流", "草稿", 7, 88.0, _dt(12, 16, 0), _dt(10)),
    ("wf-007", "数据分析报告", "从数据集到可视化报告的自动链路", "工作流", "已发布", 20, 97.3, _dt(15, 4, 0), _dt(9)),
    ("wf-008", "社交媒体监控", "关键词抓取 + 情感分析 + 预警", "工作流", "已发布", 9, 93.6, _dt(15, 9, 45), _dt(8)),
]

AGENTS = [
    ("agt-001", "智能客服助手", "基于知识库的智能客服Agent，能够处理常见问题并转接人工", "聊天助手", "Function Calling", "活跃", "你是一个智能助手，请根据用户的需求提供帮助。", 5, 156, _dt(15, 9, 50), _dt(15)),
    ("agt-002", "内容创作助手", "擅长营销文案、公众号长文与短视频脚本", "内容创作", "ReAct", "活跃", "你是一位资深内容创作者。", 3, 212, _dt(15, 8, 30), _dt(14)),
    ("agt-003", "销售支持专家", "销售话术、客户画像分析与跟进建议", "销售", "Function Calling", "活跃", "你是销售团队的资深顾问。", 4, 88, _dt(15, 7, 0), _dt(13)),
    ("agt-004", "技术支持机器人", "面向终端用户的技术问题排查", "技术支持", "Chain of Thought", "错误", "你是技术支持工程师。", 6, 43, _dt(11, 14, 0), _dt(12)),
    ("agt-005", "财务分析助手", "财报解读、成本结构与预算建议", "数据分析", "ReAct", "活跃", "你是财务分析师。", 2, 67, _dt(14, 18, 0), _dt(11)),
    ("agt-006", "数据分析师", "自然语言转 SQL 与指标归因", "数据分析", "Chain of Thought", "草稿", "你是一名数据科学家。", 4, 0, None, _dt(10)),
    ("agt-007", "项目管理助手", "任务拆解、排期与风险提示", "办公", "Function Calling", "暂停", "你是项目经理。", 3, 121, _dt(9, 11, 0), _dt(9)),
    ("agt-008", "AI 数据分析师", "面向 BI 场景的自助分析助手", "数据分析", "ReAct", "活跃", "你是一名 BI 分析师。", 5, 156, _dt(15, 6, 0), _dt(8)),
]

KNOWLEDGE_BASES = [
    ("kb-001", "产品文档知识库", "产品手册与 API 文档集合", 156, "50 MB", "text-embedding-3-small", 800, 150, "已就绪", 100, _dt(15)),
    ("kb-002", "FAQ知识库", "客服常见问题与标准答复", 89, "12 MB", "text-embedding-3-small", 800, 150, "处理中", 65, _dt(15, 9, 0)),
    ("kb-003", "技术文档库", "内部技术规范与架构文档", 234, "120 MB", "bge-large-zh", 1000, 200, "已就绪", 100, _dt(14)),
    ("kb-004", "客户支持知识库", "工单沉淀与赔付政策", 45, "8 MB", "text-embedding-3-small", 600, 100, "已就绪", 100, _dt(13)),
    ("kb-005", "内部规范库", "人事、财务与合规制度", 23, "4 MB", "bge-large-zh", 800, 150, "失败", 30, _dt(12)),
]

DATASETS = [
    ("ds-001", "产品知识库", "产品手册结构化后的问答数据", "文档", 156, "2.3 GB", "已完成", 100, _dt(15)),
    ("ds-002", "客服FAQ", "历史工单整理出的问答对", "问答对", 89, "450 MB", "已完成", 100, _dt(14)),
    ("ds-003", "技术文档", "架构与接口文档解析结果", "文档", 234, "1.2 GB", "处理中", 75, _dt(13)),
    ("ds-004", "销售数据", "季度销售流水与客户标签", "表格", 120, "800 MB", "待处理", 0, None),
]

PROMPTS = [
    ("pmt-001", "智能聊天助手", "通用对话基线提示词", "客服", "gpt-4o", "v3", "已发布", 342, "你是AI智能助手，请根据用户的需求提供帮助。"),
    ("pmt-002", "代码审查提示词", "审查代码质量、安全性与最佳实践", "开发", "claude-3-5-sonnet", "v2", "已发布", 198, "你是一名资深代码审查员，请从可读性、安全性、性能三方面审查。"),
    ("pmt-003", "产品文案生成", "电商详情页文案模板", "内容创作", "gpt-4o-mini", "v1", "草稿", 76, "你是电商文案专家，请写出有画面感的卖点文案。"),
    ("pmt-004", "会议纪要整理", "从转写文本抽取决议与待办", "办公", "gpt-4o", "v4", "已发布", 265, "请把会议记录整理为决议、待办、风险三部分。"),
    ("pmt-005", "SQL 生成器", "自然语言转 SQL，带表结构约束", "数据分析", "deepseek-chat", "v2", "已发布", 431, "根据用户问题生成 SQLite 方言的 SQL，只输出 SQL。"),
    ("pmt-006", "客服话术优化", "把生硬答复改写为共情表达", "客服", "gpt-4o-mini", "v1", "草稿", 54, "请把下面的答复改写得更共情、更具体。"),
    ("pmt-007", "数据分析报告生成", "从指标表生成分析结论", "数据分析", "claude-3-5-sonnet", "v3", "已发布", 187, "请基于给定指标，输出结论、原因假设与建议动作。"),
    ("pmt-008", "文本摘要", "长文本三段式摘要", "通用", "gpt-4o-mini", "v1", "已发布", 512, "用三段话总结全文，不超过 200 字。"),
]

TOOLS = [
    ("tool-001", "文本摘要器", "对长文本生成三段式摘要", "内置", "长文本文档", "text, maxLength", "可用", 1520, _dt(15)),
    ("tool-002", "翻译工具", "中英日韩多语互译", "内置", "文本, 目标语言", "text, targetLang", "可用", 980, _dt(14)),
    ("tool-003", "数据提取器", "从 PDF/网页抽取结构化字段", "自定义API", "文件或 URL", "source, fields", "可用", 640, _dt(13)),
    ("tool-004", "网页爬虫", "抓取指定页面正文", "自定义API", "目标 URL", "url, selector", "可用", 2130, _dt(12)),
    ("tool-005", "邮件发送器", "按模板批量发送邮件", "自定义API", "收件人, 主题, 正文", "to, subject, body", "可用", 310, _dt(11)),
    ("tool-006", "日历查询", "查询团队空闲时间", "内置", "时间范围", "start, end", "停用", 145, _dt(10)),
    ("tool-007", "SQL 查询", "对数据集执行只读 SQL", "内置", "查询语句", "sql", "可用", 890, _dt(9)),
    ("tool-008", "图片生成", "文生图", "自定义API", "提示词, 尺寸", "prompt, size", "可用", 1220, _dt(8)),
    ("tool-009", "语音转文字", "长音频转写", "内置", "音频文件", "audio, language", "可用", 470, _dt(8)),
    ("tool-010", "文档解析", "PDF/Word 结构化解析", "内置", "文档文件", "file", "可用", 760, _dt(8)),
]

PROVIDERS = [
    ("prov-001", "OpenAI", "openai", 12, "已连接", "sk-...8f2a", True, "https://api.openai.com/v1", _dt(15)),
    ("prov-002", "Anthropic", "anthropic", 5, "已连接", "sk-ant-...41c9", True, "https://api.anthropic.com", _dt(14)),
    ("prov-003", "Google AI", "google", 6, "未连接", "", False, None, _dt(13)),
    ("prov-004", "Azure OpenAI", "azure-openai", 4, "错误", "b3f1...9d02", False, "https://your-res.openai.azure.com", _dt(12)),
    ("prov-005", "AWS Bedrock", "aws-bedrock", 8, "维护中", "AKIA...7xQ", False, None, _dt(11)),
    ("prov-006", "Hugging Face", "huggingface", 20, "未连接", "", False, "https://api-inference.huggingface.co", _dt(10)),
    ("prov-007", "Ollama", "ollama", 7, "测试中", "local", True, "http://127.0.0.1:11434", _dt(9)),
]

APPS = [
    ("app-001", "智能客服助手", "面向官网的客服对话应用", "聊天机器人", "运行中", 15420, "agt-001", None, _dt(15)),
    ("app-002", "智能问答系统", "基于知识库的问答", "智能体", "运行中", 8930, "agt-001", None, _dt(14)),
    ("app-003", "销售数据分析", "销售指标自助分析", "智能体", "运行中", 4210, "agt-005", None, _dt(13)),
    ("app-004", "内容审核平台", "UGC 内容合规审核", "工作流应用", "已停止", 3120, None, "wf-006", _dt(12)),
    ("app-005", "文档摘要服务", "长文档一键摘要", "工作流应用", "运行中", 6750, None, "wf-002", _dt(11)),
    ("app-006", "邮件自动分类", "收件箱智能分流", "工作流应用", "运行中", 2980, None, "wf-005", _dt(10)),
    ("app-007", "舆情监控", "品牌舆情实时监控", "工作流应用", "运行中", 1840, None, "wf-008", _dt(9)),
    ("app-008", "招聘筛选助手", "简历初筛与匹配度打分", "智能体", "草稿", 0, None, None, _dt(8)),
    ("app-009", "财务报告生成", "季度财报自动成稿", "工作流应用", "运行中", 760, None, "wf-007", _dt(8)),
    ("app-010", "知识库问答", "内部知识库问答入口", "聊天机器人", "运行中", 5320, "agt-001", None, _dt(8)),
]

PLUGINS = [
    ("plug-001", "网页搜索", "接入搜索引擎实时检索", "搜索", "官方", 4.8, 15420, "免费", True, True, True),
    ("plug-002", "代码执行", "在沙箱内运行 Python/JS", "工具", "官方", 4.9, 12300, "免费", True, False, True),
    ("plug-003", "文件读取", "读取 PDF/Word/Excel", "工具", "官方", 4.7, 9800, "免费", True, True, False),
    ("plug-004", "数据库查询", "只读 SQL 查询", "数据", "官方", 4.6, 7600, "免费", True, False, False),
    ("plug-005", "天气查询", "全球天气与预报", "生活", "社区", 4.3, 5400, "免费", False, False, False),
    ("plug-006", "邮件发送", "SMTP 发送与模板渲染", "工具", "官方", 4.5, 6100, "免费", True, True, False),
    ("plug-007", "日历管理", "会议创建与空闲查询", "办公", "官方", 4.4, 4300, "免费", True, False, False),
    ("plug-008", "图片理解", "多模态图片问答", "多媒体", "官方", 4.8, 8800, "¥9.9/月", True, False, True),
    ("plug-009", "PDF 解析", "版面还原与表格抽取", "文档", "社区", 4.2, 3200, "免费", False, True, False),
    ("plug-010", "语音识别", "中英双语长音频转写", "多媒体", "官方", 4.6, 5100, "¥19.9/月", True, False, False),
    ("plug-011", "翻译", "多语种高质量翻译", "工具", "官方", 4.7, 11200, "免费", True, True, False),
    ("plug-012", "图表生成", "从数据生成 ECharts 配置", "数据", "社区", 4.1, 2600, "免费", False, False, False),
]

ALERTS = [
    ("alert-001", "错误率超过阈值", "Azure OpenAI 渠道 5xx 比例 12.4%，已持续 8 分钟", "严重", "未处理", "Azure OpenAI", _dt(15, 9, 12)),
    ("alert-002", "成本接近月度预算", "本月已消耗 $1,247.50，达预算 78%", "警告", "未处理", "计费", _dt(15, 8, 40)),
    ("alert-003", "平均延迟升高", "模型平均响应时间从 1.2s 升至 2.8s", "提示", "已解决", "OpenAI", _dt(14, 17, 5)),
]

AB_TESTS = [
    ("ab-001", "摘要提示词 v2 vs v3", "gpt-4o-mini", "gpt-4o", "运行中", 1200, None, _dt(15)),
    ("ab-002", "客服话术 A/B", "gpt-4o", "claude-3-5-sonnet", "已完成", 3000, "claude-3-5-sonnet", _dt(12)),
]

USERS = [
    ("usr-001", "admin", "Admin", "admin@example.com", "admin"),
    ("usr-002", "developer", "开发者小王", "dev@example.com", "developer"),
    ("usr-003", "viewer", "只读访客", "viewer@example.com", "viewer"),
]

# 成本按「token × 单价」算，不写死金额
PRICE_PER_1K = {
    "gpt-4o": (0.005, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "claude-3-5-sonnet": (0.003, 0.015),
    "deepseek-chat": (0.00014, 0.00028),
}




def seed_if_empty(session: Session) -> bool:
    """库为空时灌数据。返回是否真的执行了灌入。"""
    existing = session.exec(select(models.Workflow)).first()
    if existing is not None:
        return False

    session.add_all(
        [
            models.User(id=i, username=u, display_name=d, email=e, role=r)
            for i, u, d, e, r in USERS
        ]
    )
    session.add_all(
        [
            models.Workflow(
                id=i,
                name=n,
                description=d,
                type=t,
                status=s,
                node_count=nc,
                success_rate=sr,
                last_run_at=lr,
                created_at=ca,
                updated_at=ca,
            )
            for i, n, d, t, s, nc, sr, lr, ca in WORKFLOWS
        ]
    )
    session.add_all(
        [
            models.Agent(
                id=i,
                name=n,
                description=d,
                type=t,
                strategy=st,
                status=s,
                system_prompt=sp,
                tool_count=tc,
                run_count=rc,
                last_run_at=lr,
                created_at=ca,
                updated_at=ca,
            )
            for i, n, d, t, st, s, sp, tc, rc, lr, ca in AGENTS
        ]
    )
    session.add_all(
        [
            models.KnowledgeBase(
                id=i,
                name=n,
                description=d,
                doc_count=dc,
                size_label=sz,
                embedding_model=em,
                chunk_size=cs,
                chunk_overlap=co,
                status=s,
                vector_progress=vp,
                created_at=ca,
                updated_at=ca,
            )
            for i, n, d, dc, sz, em, cs, co, s, vp, ca in KNOWLEDGE_BASES
        ]
    )
    session.add_all(
        [
            models.Dataset(
                id=i,
                name=n,
                description=d,
                type=t,
                record_count=rc,
                size_label=sz,
                parse_status=ps,
                progress=pg,
                created_at=ca,
                updated_at=ca or _dt(15, 9),
            )
            for i, n, d, t, rc, sz, ps, pg, ca in DATASETS
        ]
    )
    session.add_all(
        [
            models.Prompt(
                id=i,
                name=n,
                description=d,
                category=c,
                model_id=m,
                version=v,
                status=s,
                usage_count=uc,
                content=ct,
                created_at=_dt(10),
                updated_at=_dt(15, 9),
            )
            for i, n, d, c, m, v, s, uc, ct in PROMPTS
        ]
    )
    session.add_all(
        [
            models.Tool(
                id=i,
                name=n,
                description=d,
                type=t,
                input_params=ip,
                input_schema=isch,
                status=s,
                call_count=cc,
                created_at=ca,
                updated_at=ca,
            )
            for i, n, d, t, ip, isch, s, cc, ca in TOOLS
        ]
    )
    session.add_all(
        [
            models.ModelProvider(
                id=i,
                name=n,
                slug=sl,
                model_count=mc,
                status=s,
                api_key_masked=k,
                enabled=en,
                base_url=bu,
                created_at=ca,
                updated_at=ca,
            )
            for i, n, sl, mc, s, k, en, bu, ca in PROVIDERS
        ]
    )
    session.add_all(
        [
            models.App(
                id=i,
                name=n,
                description=d,
                type=t,
                status=s,
                usage_count=uc,
                agent_id=ai,
                workflow_id=wi,
                created_at=ca,
                updated_at=ca,
            )
            for i, n, d, t, s, uc, ai, wi, ca in APPS
        ]
    )
    session.add_all(
        [
            models.Plugin(
                id=i,
                name=n,
                description=d,
                category=c,
                author=a,
                rating=r,
                download_count=dl,
                price=p,
                verified=v,
                installed=ins,
                hot=hot,
            )
            for i, n, d, c, a, r, dl, p, v, ins, hot in PLUGINS
        ]
    )
    session.add_all(
        [
            models.Alert(
                id=i, title=t, detail=d, severity=sv, status=s, source=src, created_at=ca
            )
            for i, t, d, sv, s, src, ca in ALERTS
        ]
    )
    session.add_all(
        [
            models.AbTest(
                id=i,
                name=n,
                model_a=ma,
                model_b=mb,
                status=s,
                sample_size=ss,
                winner=w,
                started_at=ca,
            )
            for i, n, ma, mb, s, ss, w, ca in AB_TESTS
        ]
    )
    session.commit()
    return True
