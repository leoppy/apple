from __future__ import annotations

import json
import os
import sys
from base64 import b64encode
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen


ENV_CANDIDATES = (
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parents[1] / ".env",
)


def load_env_file() -> None:
    path = next((item for item in ENV_CANDIDATES if item.exists()), None)
    if path is None:
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"缺少环境变量: {name}")
    return value


def build_job_api_url(base_url: str, pipeline_name: str) -> str:
    normalized = base_url.rstrip("/") + "/"
    path_parts = [quote(part, safe="") for part in pipeline_name.split("/") if part]
    job_path = "/".join(f"job/{part}" for part in path_parts)
    return urljoin(normalized, f"{job_path}/api/json")


def fetch_job_info(api_url: str, username: str, token: str) -> tuple[int, dict[str, object] | None]:
    auth = b64encode(f"{username}:{token}".encode("utf-8")).decode("ascii")
    request = Request(
        api_url,
        headers={
            "Authorization": f"Basic {auth}",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=15) as response:
            payload = response.read().decode("utf-8")
            return response.status, json.loads(payload)
    except HTTPError as exc:
        if exc.code == 404:
            return 404, None
        details = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Jenkins API 返回 HTTP {exc.code}: {details}") from exc
    except URLError as exc:
        raise RuntimeError(f"无法连接 Jenkins: {exc}") from exc


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python check_pipeline.py <jenkins-job-name>")
        return 2

    pipeline_name = sys.argv[1]
    load_env_file()
    base_url = require_env("JENKINS_URL")
    username = require_env("JENKINS_USER")
    token = require_env("JENKINS_TOKEN")

    api_url = build_job_api_url(base_url, pipeline_name)
    status, payload = fetch_job_info(api_url, username, token)

    if status == 404 or payload is None:
        print(f"未找到流水线: {pipeline_name}")
        print(f"查询地址: {api_url}")
        return 1

    print(f"已找到流水线: {payload.get('name', pipeline_name)}")
    print(f"URL: {payload.get('url', 'N/A')}")
    print(f"类型: {payload.get('_class', 'N/A')}")
    print(f"状态码: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
