from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

import requests
from dotenv import load_dotenv


class ConfluenceClient:
    def __init__(
        self,
        base_url: str,
        auth_mode: str,
        api_token: str,
        username: str = "",
        timeout: int = 30,
        retry_times: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_times = retry_times
        self.auth_mode = auth_mode
        self.username = username
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        if self.auth_mode == "bearer":
            self.session.headers.update({"Authorization": f"Bearer {self.api_token}"})
        else:
            self.session.auth = (self.username, self.api_token)

    @classmethod
    def from_env(cls, timeout: int = 30, retry_times: int = 3) -> "ConfluenceClient":
        env_path = Path(__file__).parent.parent.parent.parent / "02_skills" / "token-manager" / ".env"
        load_dotenv(dotenv_path=env_path)
        base_url = os.getenv("CONFLUENCE_URL", "").strip()
        username = os.getenv("CONFLUENCE_USERNAME", "").strip()
        api_token = os.getenv("CONFLUENCE_API_TOKEN", "").strip()
        if not base_url or not username or not api_token:
            raise ValueError("Confluence 配置缺失，请检查 .env 中的 CONFLUENCE_URL/USERNAME/API_TOKEN")
        auth_mode = os.getenv("CONFLUENCE_AUTH_MODE", "bearer").strip().lower()
        if auth_mode not in {"bearer", "basic"}:
            raise ValueError("CONFLUENCE_AUTH_MODE 只支持 bearer/basic")
        return cls(
            base_url=base_url,
            auth_mode=auth_mode,
            api_token=api_token,
            username=username,
            timeout=timeout,
            retry_times=retry_times,
        )

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        last_error: Exception | None = None
        for _ in range(self.retry_times):
            try:
                resp = self.session.request(method=method, url=url, **kwargs)
                resp.raise_for_status()
                return resp
            except Exception as ex:  # noqa: BLE001
                last_error = ex
        raise RuntimeError(f"Confluence 请求失败: {url}, error={last_error}")

    def get_page(self, page_id: str) -> Dict:
        resp = self._request("GET", f"/rest/api/content/{page_id}")
        return resp.json()

    def get_child_pages(self, page_id: str) -> List[Dict]:
        start = 0
        limit = 100
        pages: List[Dict] = []
        while True:
            resp = self._request(
                "GET",
                f"/rest/api/content/{page_id}/child/page?limit={limit}&start={start}",
            ).json()
            chunk = resp.get("results", [])
            pages.extend(chunk)
            if len(chunk) < limit:
                break
            start += limit
        return pages

    def get_descendant_pages(self, root_page_id: str) -> List[Dict]:
        queue = [str(root_page_id)]
        collected: List[Dict] = []
        while queue:
            current = queue.pop(0)
            children = self.get_child_pages(current)
            collected.extend(children)
            queue.extend(str(item["id"]) for item in children if item.get("id"))
        return collected

    def get_page_attachments(self, page_id: str) -> List[Dict]:
        start = 0
        limit = 100
        files: List[Dict] = []
        while True:
            resp = self._request(
                "GET",
                f"/rest/api/content/{page_id}/child/attachment?limit={limit}&start={start}&expand=version",
            ).json()
            chunk = resp.get("results", [])
            files.extend(chunk)
            if len(chunk) < limit:
                break
            start += limit
        return files

    def download_attachment(self, attachment: Dict, save_path: Path) -> Path:
        links = attachment.get("_links", {})
        download_link = links.get("download")
        if not download_link:
            raise ValueError(f"附件缺少下载链接: {attachment.get('id')}")
        url = f"{self.base_url}{download_link}"
        last_error: Exception | None = None
        for _ in range(self.retry_times):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                resp.raise_for_status()
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_bytes(resp.content)
                return save_path
            except Exception as ex:  # noqa: BLE001
                last_error = ex
        raise RuntimeError(f"下载附件失败: {url}, error={last_error}")
