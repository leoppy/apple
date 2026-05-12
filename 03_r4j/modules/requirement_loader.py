from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

from .models import Requirement


class RequirementLoader:
    def __init__(self, config: Dict, use_cache: bool = True):
        self.config = config
        self.use_cache = use_cache
        cache_cfg = config.get("cache", {})
        self.cache_enabled = bool(cache_cfg.get("enabled", True)) and use_cache
        self.cache_dir = Path(cache_cfg.get("dir", "tempFile/cache"))
        self.cache_ttl_hours = int(cache_cfg.get("ttl_hours", 24))

        api_cfg = config.get("api", {})
        self.timeout = int(api_cfg.get("timeout", 30))
        self.retry_times = int(api_cfg.get("retry_times", 3))
        self.delay_ms = int(api_cfg.get("delay_ms", 2000))

        env_path = Path(__file__).parent.parent.parent.parent / "02_skills" / "token-manager" / ".env"
        load_dotenv(dotenv_path=env_path)
        self.jira_token = os.getenv("JIRA_TOKEN", "").strip()
        self.jira_url = os.getenv("JIRA_URL", "https://jira.i-soft.com.cn").strip().rstrip("/")
        if not self.jira_token:
            raise ValueError("JIRA_TOKEN 缺失，请检查 .env")

    @property
    def api_url(self) -> str:
        return f"{self.jira_url}/rest/com.easesolutions.jira.plugins.requirements/1.0/tree/data"

    def load_all_projects(self, project_filter: Optional[str] = None) -> Dict[str, Requirement]:
        requirements: Dict[str, Requirement] = {}
        for project in self.config.get("r4j_projects", []):
            name = str(project.get("name", "")).strip()
            if project_filter and project_filter not in name:
                continue
            items = self.export_project(
                node_id=int(project["node_id"]),
                project_id=int(project["project_id"]),
                project_name=name,
                level=str(project["level"]),
            )
            for item in items:
                key = str(item.get("key", "")).strip()
                if not key:
                    continue
                requirements[key] = Requirement(
                    key=key,
                    name=str(item.get("name", "")).strip(),
                    level=str(project["level"]),
                    project_name=name,
                    project_id=int(project["project_id"]),
                    node_id=int(project["node_id"]),
                    parent_id=item.get("parent_id"),
                    description=str(item.get("description", "")).strip(),
                )
        return requirements

    def _cache_file(self, node_id: int, project_id: int) -> Path:
        return self.cache_dir / f"requirements_{project_id}_{node_id}.json"

    def _load_cache(self, cache_file: Path) -> List[Dict] | None:
        if not (self.cache_enabled and cache_file.exists()):
            return None
        age_seconds = time.time() - cache_file.stat().st_mtime
        if age_seconds > self.cache_ttl_hours * 3600:
            return None
        return json.loads(cache_file.read_text(encoding="utf-8"))

    def _save_cache(self, cache_file: Path, data: List[Dict]) -> None:
        if not self.cache_enabled:
            return
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def export_project(self, node_id: int, project_id: int, project_name: str, level: str) -> List[Dict]:
        cache_file = self._cache_file(node_id=node_id, project_id=project_id)
        cached = self._load_cache(cache_file)
        if cached is not None:
            return cached

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.jira_token}",
            "X-Atlassian-Token": "no-check",
        }

        queue: List[tuple[int, int]] = [(node_id, 0)]
        items: List[Dict] = []
        while queue:
            folder_id, current_level = queue.pop(0)
            payload = {
                "folderId": folder_id,
                "offset": 0,
                "projectId": project_id,
                "queryParams": str(folder_id),
            }
            data = self._post_json(headers=headers, payload=payload)
            item_list = data.get("itemList", [])
            for item in item_list:
                item_type = "Issue" if item.get("key") else "Folder"
                transformed = {
                    "id": item.get("id"),
                    "key": item.get("key", ""),
                    "name": item.get("name", ""),
                    "type": item_type,
                    "parent_id": folder_id,
                    "level": current_level + 1,
                    "position": item.get("position", 0),
                    "description": item.get("description", ""),
                    "project_name": project_name,
                    "v_level": level,
                }
                items.append(transformed)
                if item.get("hasChild"):
                    queue.append((int(item["id"]), current_level + 1))
            time.sleep(self.delay_ms / 1000)

        self._save_cache(cache_file, items)
        return items

    def _post_json(self, headers: Dict, payload: Dict) -> Dict:
        last_error: Exception | None = None
        for _ in range(self.retry_times):
            try:
                resp = requests.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as ex:  # noqa: BLE001
                last_error = ex
        raise RuntimeError(f"Jira 请求失败: {payload}, error={last_error}")
