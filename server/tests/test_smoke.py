"""冒烟测试：覆盖健康检查、9 个 CRUD 的分页/搜索/筛选、详情 404、创建→改→删闭环、
工作流运行、LLMOps 聚合、登录。目的是「接口形状与种子数据都对了」，不做业务边界穷举。
"""

from fastapi.testclient import TestClient


def test_health_and_seed(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["seed_ready"] is True


def test_workflow_list_pagination(client: TestClient) -> None:
    resp = client.get("/api/workflows")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 8
    assert len(body["items"]) == 8

    paged = client.get("/api/workflows", params={"page": 2, "size": 3}).json()
    assert paged["total"] == 8
    assert len(paged["items"]) == 3
    assert paged["page"] == 2


def test_workflow_search_and_filter(client: TestClient) -> None:
    hit = client.get("/api/workflows", params={"q": "客服"}).json()
    assert hit["total"] >= 1
    assert all("客服" in item["name"] or "客服" in item["description"] for item in hit["items"])

    draft = client.get("/api/workflows", params={"status": "草稿"}).json()
    assert draft["total"] == 2
    assert all(item["status"] == "草稿" for item in draft["items"])

    chat = client.get("/api/workflows", params={"type": "聊天流"}).json()
    assert chat["total"] == 2


def test_workflow_detail_and_404(client: TestClient) -> None:
    ok = client.get("/api/workflows/wf-001")
    assert ok.status_code == 200
    assert ok.json()["name"] == "智能客服工作流"
    assert ok.json()["node_count"] == 8

    missing = client.get("/api/workflows/not-exist")
    assert missing.status_code == 404


def test_workflow_create_update_delete(client: TestClient) -> None:
    created = client.post(
        "/api/workflows",
        json={"name": "新建测试工作流", "description": "冒烟测试", "type": "工作流"},
    )
    assert created.status_code == 201
    item = created.json()
    assert item["name"] == "新建测试工作流"
    assert item["id"].startswith("wf-")

    patched = client.patch(f"/api/workflows/{item['id']}", json={"name": "改名后的工作流"})
    assert patched.status_code == 200
    assert patched.json()["name"] == "改名后的工作流"

    deleted = client.delete(f"/api/workflows/{item['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/workflows/{item['id']}").status_code == 404


def test_all_resource_lists_are_seeded(client: TestClient) -> None:
    expectations = {
        "/api/agents": 8,
        "/api/knowledge-bases": 5,
        "/api/datasets": 4,
        "/api/prompts": 8,
        "/api/tools": 10,
        "/api/providers": 7,
        "/api/apps": 10,
        "/api/plugins": 12,
    }
    for path, expected in expectations.items():
        resp = client.get(path)
        assert resp.status_code == 200, path
        assert resp.json()["total"] == expected, path


def test_workflow_run_produces_trace(client: TestClient) -> None:
    resp = client.post("/api/workflows/wf-001/run", json={"input": "订单什么时候到"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["runId"].startswith("run-")
    assert body["status"] == "成功"
    assert len(body["steps"]) == 8  # wf-001 是 8 节点
    assert body["steps"][-1]["nodeType"] == "end"
    assert body["tokens"]["prompt"] > 0
    # 运行后 last_run_at 应被刷新
    assert client.get("/api/workflows/wf-001").json()["last_run_at"] is not None


def test_knowledge_documents_starts_empty(client: TestClient) -> None:
    """P2 起文档是真实上传的：种子库里没有文档，列表必须为空而不是编 4 条。"""
    resp = client.get("/api/knowledge-bases/kb-005/documents")
    assert resp.status_code == 200
    assert resp.json() == []

    assert client.get("/api/knowledge-bases/kb-404/documents").status_code == 404


def test_llmops_aggregations_reflect_real_calls(client: TestClient) -> None:
    """P1 起 LLMOps 不再读种子：数字必须来自真实调用的 trace。"""
    before = client.get("/api/llmops/overview").json()["cards"]["totalCalls"]

    # 真跑一次对话（会写 trace）
    with client.stream("POST", "/api/chat/stream", json={"input": "你好"}) as response:
        assert response.status_code == 200
        "".join(response.iter_text())

    overview = client.get("/api/llmops/overview").json()
    assert overview["cards"]["totalCalls"] == before + 1
    assert 0 < overview["cards"]["successRate"] <= 100
    assert len(overview["health"]) == 7

    series = client.get("/api/llmops/cost/series").json()
    assert len(series["series"]) >= 1
    assert series["models"], "至少应出现一次调用的模型"
    # 每天的 total 等于各模型之和
    first = series["series"][-1]
    model_sum = sum(first[m] for m in series["models"])
    assert abs(model_sum - first["total"]) < 1e-6

    perf = client.get("/api/llmops/models").json()
    assert perf and all(row["calls"] > 0 for row in perf)


def test_auth_login_and_me(client: TestClient) -> None:
    ok = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert ok.status_code == 200
    token = ok.json()["token"]
    assert token == "dev-admin"

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "admin"

    bad = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert bad.status_code == 401


def test_meta_overview(client: TestClient) -> None:
    body = client.get("/api/meta/overview").json()
    assert body["counts"]["workflows"] == 8
    assert body["counts"]["plugins"] == 12
    assert body["explore"]["totalUsage"] > 0


def test_sort_order_both_directions(client: TestClient) -> None:
    asc = client.get(
        "/api/workflows", params={"sort": "node_count", "order": "asc", "size": 5}
    ).json()
    asc_values = [item["node_count"] for item in asc["items"]]
    assert asc_values == sorted(asc_values)

    desc = client.get(
        "/api/workflows", params={"sort": "node_count", "order": "desc", "size": 5}
    ).json()
    desc_values = [item["node_count"] for item in desc["items"]]
    assert desc_values == sorted(desc_values, reverse=True)

    # 非法方向由 Pydantic 拦在 422，不会静默忽略
    assert client.get("/api/workflows", params={"order": "sideways"}).status_code == 422

    # 不存在的排序字段回落到 id，不报 500
    fallback = client.get("/api/workflows", params={"sort": "not_a_field"}).json()
    assert fallback["total"] == 8

def test_login_accepts_email(client: TestClient) -> None:
    """登录页字段写的是「邮箱地址」，所以邮箱也要能登录。"""
    resp = client.post(
        "/api/auth/login", json={"username": "admin@example.com", "password": "admin123"}
    )
    assert resp.status_code == 200
    assert resp.json()["token"] == "dev-admin"

    # 账号不存在与密码错误返回同一个 401，避免泄露账号是否存在
    bad = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    assert bad.status_code == 401

def test_chat_status_reports_mode(client: TestClient) -> None:
    body = client.get("/api/chat/status").json()
    assert body["mode"] == "mock"
    assert body["useReal"] is False
    assert body["hasKey"] is False


def test_chat_stream_emits_sse_events(client: TestClient) -> None:
    """没有 Key 时必须回落 mock，并且在 result 事件里如实回报 mode。"""
    with client.stream(
        "POST", "/api/chat/stream", json={"prompt": "你是助手", "input": "你好"}
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        payload = "".join(response.iter_text())

    assert '[DONE]' in payload

    # SSE 里每片 delta 是独立 JSON，必须拼回全文再断言
    import json

    text = ''
    result: dict = {}
    for line in payload.splitlines():
        if not line.startswith('data:') or line.strip() == 'data: [DONE]':
            continue
        event = json.loads(line[5:].strip())
        if event.get('type') == 'delta':
            text += event.get('content', '')
        elif event.get('type') == 'result':
            result = event

    assert result.get('mode') == 'mock'
    assert result['usage']['completionTokens'] > 0
    # 模拟输出里应带上「未配置 Key」的说明，而不是假装成真的
    assert '未配置模型 API Key' in text


def test_provider_test_without_key(client: TestClient) -> None:
    body = client.post("/api/providers/prov-001/test").json()
    assert body["ok"] is False
    assert body["needsKey"] is True
    assert body["envVar"] == "APP_OPENAI_API_KEY"


def test_provider_test_rejects_unknown_slug(client: TestClient) -> None:
    # google 不在支持列表里，应给出「不支持」而不是假装成功
    body = client.post("/api/providers/prov-003/test").json()
    assert body["ok"] is False
    assert body["supported"] is False

def test_chat_persists_conversation_messages_and_trace(client: TestClient) -> None:
    """一次对话 = 1 条会话 + 2 条消息 + 1 条 trace。"""
    with client.stream(
        "POST",
        "/api/chat/stream",
        json={"prompt": "你是助手", "input": "退款要几天", "prompt_id": "pmt-001"},
    ) as response:
        assert response.status_code == 200
        payload = "".join(response.iter_text())

    import json

    conversation_id = None
    for line in payload.splitlines():
        if not line.startswith("data:") or line.strip() == "data: [DONE]":
            continue
        event = json.loads(line[5:].strip())
        if event.get("type") == "result":
            conversation_id = event.get("conversationId")

    assert conversation_id, "result 事件必须回传 conversationId"

    detail = client.get(f"/api/conversations/{conversation_id}").json()
    conversation = detail["conversation"]
    assert conversation["source"] == "prompt_test"
    assert conversation["prompt_id"] == "pmt-001"
    assert conversation["message_count"] == 2

    roles = [m["role"] for m in detail["messages"]]
    assert roles == ["user", "assistant"]
    assert detail["messages"][1]["mode"] == "mock"
    assert detail["messages"][1]["content"]

    traces = detail["traces"]
    assert len(traces) == 1
    assert traces[0]["kind"] == "prompt_test"
    assert traces[0]["status"] == "成功"
    assert traces[0]["mode"] == "mock"


def test_conversations_list_and_delete(client: TestClient) -> None:
    with client.stream("POST", "/api/chat/stream", json={"input": "会话列表测试"}) as response:
        "".join(response.iter_text())

    listed = client.get("/api/conversations", params={"source": "prompt_test", "size": 50}).json()
    assert listed["total"] >= 1
    assert all(item["source"] == "prompt_test" for item in listed["items"])

    target = listed["items"][0]["id"]
    assert client.delete(f"/api/conversations/{target}").status_code == 204
    assert client.get(f"/api/conversations/{target}").status_code == 404


def test_traces_endpoint_filters(client: TestClient) -> None:
    with client.stream("POST", "/api/chat/stream", json={"input": "trace 过滤测试"}) as response:
        "".join(response.iter_text())

    traces = client.get("/api/traces", params={"kind": "prompt_test", "size": 5}).json()
    assert traces["total"] >= 1
    assert all(item["kind"] == "prompt_test" for item in traces["items"])
    assert all(item["provider"] for item in traces["items"])

def _upload_text(client: TestClient, kb_id: str, name: str, content: str) -> dict:
    response = client.post(
        f"/api/knowledge-bases/{kb_id}/documents",
        files={"file": (name, content.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_rag_upload_creates_chunks_and_vectors(client: TestClient) -> None:
    """上传 → 切块 → 向量入库，文档状态变「已入库」，知识库统计同步更新。"""
    kb = client.get("/api/knowledge-bases/kb-001/documents").json()
    assert kb == [] or all(item["status"] in {"已入库", "失败"} for item in kb)

    content = "退款政策：签收后七天内可无理由退款。运费由买家承担。\n\n" * 120
    doc = _upload_text(client, "kb-001", "退款政策.txt", content)
    assert doc["chunks"] > 1, "长文本应被切成多块"
    assert doc["status"] == "已入库"
    assert doc["mode"] == "mock"  # 测试环境强制 mock

    listed = client.get("/api/knowledge-bases/kb-001/documents").json()
    assert any(item["id"] == doc["id"] for item in listed)

    chunks = client.get(f"/api/knowledge-bases/kb-001/documents/{doc['id']}/chunks").json()
    assert chunks["total"] == doc["chunks"] > 1
    assert chunks["chunks"][0]["position"] == 0
    assert chunks["chunks"][0]["content"]

    kb_row = client.get("/api/knowledge-bases/kb-001").json()
    assert kb_row["doc_count"] >= 1
    assert kb_row["chunk_count"] >= doc["chunks"]


def test_rag_search_returns_scored_hits(client: TestClient) -> None:
    """检索要能真的命中：分数降序、带来源文档与片段。"""
    body = {
        "query": "退款几天到账",
        "top_k": 3,
    }
    result = client.post("/api/knowledge-bases/kb-001/search", json=body).json()

    assert result["scanned"] > 0
    assert result["hits"], "应该至少命中一块"
    scores = [hit["score"] for hit in result["hits"]]
    assert scores == sorted(scores, reverse=True)
    assert all(hit["docName"] for hit in result["hits"])
    assert result["mode"] == "mock"


def test_rag_rejects_unsupported_and_empty(client: TestClient) -> None:
    bad = client.post(
        "/api/knowledge-bases/kb-001/documents",
        files={"file": ("x.exe", b"binary", "application/octet-stream")},
    )
    assert bad.status_code == 415

    empty = client.post(
        "/api/knowledge-bases/kb-001/documents",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert empty.status_code == 400


def test_rag_delete_document_cleans_chunks(client: TestClient) -> None:
    doc = _upload_text(client, "kb-002", "临时文档.txt", "这是一段用于删除测试的文本。" * 30)
    assert doc["chunks"] >= 1

    assert (
        client.delete(f"/api/knowledge-bases/kb-002/documents/{doc['id']}").status_code == 204
    )
    listed = client.get("/api/knowledge-bases/kb-002/documents").json()
    assert all(item["id"] != doc["id"] for item in listed)
    # 该库已无分块，检索应返回空而不是报错
    result = client.post(
        "/api/knowledge-bases/kb-002/search", json={"query": "删除测试", "top_k": 3}
    ).json()
    assert result["hits"] == []
