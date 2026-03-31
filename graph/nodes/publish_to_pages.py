import os
import json
import base64
import logging
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from graph.state import State

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
BJT = timezone(timedelta(hours=8))


def publish_to_pages(state: State) -> dict:
    """将 HTML 内容发布到 GitHub Pages 仓库。"""
    token = os.environ["GITHUB_PAGES_TOKEN"]
    repo = os.environ.get("GITHUB_PAGES_REPO", "Woody-Empire/daily-news-site")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    today = datetime.now(BJT).strftime("%Y-%m-%d")
    content_path = f"content/money-stuff/{today}.html"
    manifest_path = "content/index.json"

    html_content = state["html_content"]

    # 1. 上传 HTML 文件
    _create_or_update_file(
        repo, headers, content_path, html_content, f"feat: add money-stuff {today}"
    )

    # 2. 更新 index.json
    manifest_file = _get_file(repo, headers, manifest_path)
    manifest_data = json.loads(manifest_file["content"])
    if today not in manifest_data.get("money-stuff", []):
        manifest_data.setdefault("money-stuff", []).insert(0, today)
        _create_or_update_file(
            repo,
            headers,
            manifest_path,
            json.dumps(manifest_data, indent=2) + "\n",
            f"feat: update manifest for {today}",
            sha=manifest_file["sha"],
        )

    logger.info("已发布 money-stuff %s 到 GitHub Pages", today)
    return {}


def _api_request(method: str, url: str, headers: dict, data: dict | None = None):
    """发送 GitHub API 请求。"""
    body = json.dumps(data).encode("utf-8") if data else None
    req = Request(url, data=body, headers=headers, method=method)
    with urlopen(req) as resp:
        return json.loads(resp.read())


def _get_file(repo: str, headers: dict, path: str) -> dict:
    """获取文件内容和 SHA。"""
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}"
    data = _api_request("GET", url, headers)
    content = base64.b64decode(data["content"]).decode("utf-8")
    return {"content": content, "sha": data["sha"]}


def _create_or_update_file(
    repo: str,
    headers: dict,
    path: str,
    content: str,
    message: str,
    sha: str | None = None,
):
    """创建或更新 GitHub 仓库中的文件。"""
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}"

    # 如果没有提供 SHA，尝试获取已有文件的 SHA
    if sha is None:
        try:
            existing = _api_request("GET", url, headers)
            sha = existing["sha"]
        except HTTPError:
            pass

    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha

    _api_request("PUT", url, headers, payload)
    logger.info("%s %s", "更新" if sha else "创建", path)
