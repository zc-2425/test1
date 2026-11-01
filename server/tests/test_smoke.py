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


def test_knowledge_documents(client: TestClient) -> None:
    resp = client.get("/api/knowledge-bases/kb-001/documents")
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 4
    assert docs[0]["status"] == "已入库"  # kb-001 进度 100


def test_llmops_aggregations(client: TestClient) -> None:
    overview = client.get("/api/llmops/overview").json()
    assert overview["cards"]["totalCalls"] > 0
    assert overview["cards"]["totalCostUsd"] > 0
    assert 0 < overview["cards"]["successRate"] <= 100
    assert len(overview["health"]) == 7

    series = client.get("/api/llmops/cost/series").json()
    assert len(series["series"]) == 15
    assert len(series["models"]) == 4
    # 每天的 total 应该等于各模型之和
    first = series["series"][0]
    model_sum = sum(first[m] for m in series["models"])
    assert abs(model_sum - first["total"]) < 1e-6

    perf = client.get("/api/llmops/models").json()
    assert len(perf) == 4
    assert all(row["calls"] > 0 for row in perf)


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
