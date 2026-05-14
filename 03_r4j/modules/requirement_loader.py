from __future__ import annotations

import json
import logging
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
        self.project_root = Path(config.get("_project_root", Path(__file__).resolve().parents[1])).resolve()
        cache_cfg = config.get("cache", {})
        self.cache_enabled = bool(cache_cfg.get("enabled", True)) and use_cache
        cache_base_dir = Path(cache_cfg.get("dir", "tempFile/cache"))
        if cache_base_dir.is_absolute():
            resolved_cache_base = cache_base_dir
        else:
            resolved_cache_base = (self.project_root / cache_base_dir).resolve()

        config_cache_namespace = str(cache_cfg.get("namespace", "")).strip()
        if not config_cache_namespace:
            config_cache_namespace = str(config.get("_config_name", "")).strip()
        if not config_cache_namespace:
            config_cache_namespace = "default"

        self.cache_dir = resolved_cache_base / config_cache_namespace
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
        issue_fields_cache = self._load_issue_fields_cache()

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
                fields = self._fetch_issue_fields(key, issue_fields_cache)
                requirements[key] = Requirement(
                    key=key,
                    name=str(item.get("name", "")).strip(),
                    level=str(project["level"]),
                    project_name=name,
                    project_id=int(project["project_id"]),
                    node_id=int(project["node_id"]),
                    parent_id=item.get("parent_id"),
                    description=str(item.get("description", "")).strip(),
                    module=fields.get("module", ""),
                    components=fields.get("components", ""),
                    issue_type=fields.get("issue_type", ""),
                    labels=fields.get("labels", ""),
                    priority=fields.get("priority", ""),
                )

        self._save_issue_fields_cache(issue_fields_cache)
        return requirements

    def _cache_file(self, node_id: int, project_id: int) -> Path:
        return self.cache_dir / "requirements" / f"requirements_{project_id}_{node_id}.json"

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
        logger = logging.getLogger(__name__)

        while queue:
            folder_id, current_level = queue.pop(0)
            payload = {
                "folderId": folder_id,
                "offset": 0,
                "projectId": project_id,
                "queryParams": str(folder_id),
            }
            try:
                data = self._post_json(headers=headers, payload=payload)
            except RuntimeError as e:
                # 如果遇到 500 错误，记录警告并跳过该文件夹
                if "500 Server Error" in str(e):
                    logger.warning(f"跳过文件夹 {folder_id}（API 返回 500 错误，可能是空文件夹）: {e}")
                    continue
                raise

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
                # 记录响应内容以便调试
                if hasattr(ex, 'response') and ex.response is not None:
                    try:
                        error_detail = ex.response.text[:500]
                        logging.getLogger(__name__).error(f"API 错误详情: {error_detail}")
                    except Exception:  # noqa: BLE001
                        pass
        raise RuntimeError(f"Jira 请求失败: {payload}, error={last_error}")

    def _issue_fields_cache_file(self) -> Path:
        return self.cache_dir / "issue_fields_cache.json"

    def _load_issue_fields_cache(self) -> Dict[str, Dict]:
        """加载 issue fields 缓存"""
        cache_file = self._issue_fields_cache_file()
        if not (self.cache_enabled and cache_file.exists()):
            return {}
        try:
            age_seconds = time.time() - cache_file.stat().st_mtime
            if age_seconds > self.cache_ttl_hours * 3600:
                return {}
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}

    def _save_issue_fields_cache(self, cache: Dict[str, Dict]) -> None:
        """保存 issue fields 缓存"""
        if not self.cache_enabled:
            return
        cache_file = self._issue_fields_cache_file()
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

    def _fetch_issue_fields(self, issue_key: str, cache: Dict[str, Dict]) -> Dict[str, str]:
        """获取 Jira issue 的多个字段信息（带缓存）"""
        if not issue_key:
            return {"module": "", "components": "", "issue_type": "", "labels": "", "priority": ""}

        # 先查缓存
        if issue_key in cache:
            return cache[issue_key]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.jira_token}",
        }

        try:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}"
            resp = requests.get(url, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            fields = data.get("fields", {})

            # 提取 components
            components = fields.get("components", [])
            component_names = [comp.get("name", "") for comp in components if comp.get("name")]
            components_str = ", ".join(component_names)
            module_str = components_str

            # 提取 issue type
            issue_type = fields.get("issuetype", {}).get("name", "")

            # 提取 labels
            labels = fields.get("labels", [])
            labels_str = ", ".join(labels) if labels else ""

            # 提取 priority
            priority = fields.get("priority", {})
            priority_str = priority.get("name", "") if priority else ""

            result = {
                "module": module_str,
                "components": components_str,
                "issue_type": issue_type,
                "labels": labels_str,
                "priority": priority_str,
            }
            cache[issue_key] = result
            return result
        except Exception:  # noqa: BLE001
            result = {"module": "", "components": "", "issue_type": "", "labels": "", "priority": ""}
            cache[issue_key] = result
            return result
