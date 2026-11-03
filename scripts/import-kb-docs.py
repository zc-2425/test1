"""把真实公开文档导入知识库。

为什么要有这个脚本：知识库内容存在本地 SQLite（`server/data/` 已被 gitignore），
换台机器就没了。把「抓哪些、怎么清洗、怎么入库」固化下来，才可复现。

用法（先启动后端）：
    server\\.venv\\Scripts\\python.exe scripts\\import-kb-docs.py --kb kb-xxxx
    server\\.venv\\Scripts\\python.exe scripts\\import-kb-docs.py --kb kb-xxxx --force

已存在的同名文档默认跳过，所以重复执行是安全的；--force 会重新上传并覆盖索引。
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request

import httpx

# (文件名, 源地址, 类型) —— 全部是公开的官方文档原文
SOURCES: list[tuple[str, str, str]] = [
    (
        "deepseek-pricing",
        "https://api-docs.deepseek.com/zh-cn/quick_start/pricing.md",
        "md",
    ),
    (
        "deepseek-chat-api",
        "https://api-docs.deepseek.com/zh-cn/api/create-chat-completion.md",
        "md",
    ),
    (
        "siliconflow-embeddings",
        "https://docs.siliconflow.cn/docs/api/embeddings-post",
        "html",
    ),
    (
        "fastapi-dependencies",
        "https://gitee.com/mirrors/fastapi/raw/master/docs/zh/docs/tutorial/dependencies/index.md",
        "md",
    ),
    (
        "fastapi-background-tasks",
        "https://raw.githubusercontent.com/fastapi/fastapi/master/docs/zh/docs/tutorial/background-tasks.md",
        "md",
    ),
    (
        "vue-reactivity",
        "https://raw.githubusercontent.com/vuejs-translations/docs-zh-cn/main/src/guide/essentials/reactivity-fundamentals.md",
        "md",
    ),
]

UA = {"User-Agent": "Mozilla/5.0 kb-importer"}


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return response.read().decode("utf-8", "replace")


def html_to_text(html: str) -> str:
    """只取正文（main/article），去掉脚本、样式与标签。"""
    for pattern in (r"(?is)<main[^>]*>(.*?)</main>", r"(?is)<article[^>]*>(.*?)</article>"):
        match = re.search(pattern, html)
        if match:
            html = match.group(1)
            break
    html = re.sub(r"(?is)<script.*?</script>", "", html)
    html = re.sub(r"(?is)<style.*?</style>", "", html)
    text = re.sub(r"(?s)<[^>]+>", "\n", html)
    for entity, char in (
        ("&nbsp;", " "),
        ("&amp;", "&"),
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&quot;", '"'),
        ("&#39;", "'"),
        ("&#x27;", "'"),
    ):
        text = text.replace(entity, char)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def read_text(url: str, kind: str) -> str:
    raw = fetch(url)
    text = html_to_text(raw) if kind == "html" else raw
    # 文档标题里的锚点标记（如 {#background-tasks}）对检索是噪声
    text = re.sub(r"\{#[a-z0-9-]+\}", "", text)
    return re.sub(r"(\r?\n){3,}", "\n\n", text).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", required=True, help="目标知识库 id")
    parser.add_argument("--base-url", default="http://127.0.0.1:5274/api")
    parser.add_argument("--force", action="store_true", help="同名文档也重新上传")
    args = parser.parse_args()

    with httpx.Client(timeout=180) as client:
        docs_url = f"{args.base_url}/knowledge-bases/{args.kb}/documents"
        probe = client.get(docs_url)
        if probe.status_code == 404:
            print(f"知识库不存在: {args.kb}")
            return 1
        existing = {item["name"] for item in probe.json()}

        total_chunks = 0
        for name, url, kind in SOURCES:
            filename = f"{name}.md"
            if filename in existing and not args.force:
                print(f"  跳过 {filename}（已存在）")
                continue
            try:
                text = read_text(url, kind)
            except Exception as exc:  # noqa: BLE001 - 单个源失败不影响其它
                print(f"  抓取失败 {filename}: {exc}")
                continue

            response = client.post(
                docs_url,
                files={"file": (filename, text.encode("utf-8"), "text/markdown")},
            )
            if response.status_code != 201:
                print(f"  入库失败 {filename}: HTTP {response.status_code} {response.text[:160]}")
                continue
            body = response.json()
            total_chunks += int(body.get("chunks", 0))
            print(
                f"  OK {filename:<28} {body['chunks']:>3} 块  {body['mode']}  {body['tookMs']}ms"
            )

        print(f"\n本次新增分块: {total_chunks}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
