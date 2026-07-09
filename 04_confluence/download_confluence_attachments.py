#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""递归下载指定 Confluence 页面及其子页面的附件。"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.local.json"
DEFAULT_DOWNLOAD_ROOT = SCRIPT_DIR / "downloads"
INVALID_PATH_CHARS = '<>:"/\\|?*'
TITLE_PATTERN = re.compile(r"^Title:\s*(.+)$", re.MULTILINE)


def create_default_config() -> None:
    default_config = {
        "page_id_or_url": "https://confluence.i-soft.com.cn/pages/viewpage.action?pageId=98519040",
        "download_root": str(DEFAULT_DOWNLOAD_ROOT),
    }
    CONFIG_PATH.write_text(
        json.dumps(default_config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_config() -> Dict[str, object]:
    if not CONFIG_PATH.exists():
        create_default_config()
        print(f"已创建配置文件: {CONFIG_PATH}")
        print("请确认配置内容后重新运行脚本。")
        sys.exit(0)

    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"配置文件不是合法 JSON: {exc}") from exc


def require_config_value(config: Dict[str, object], key: str) -> str:
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"配置项 `{key}` 缺失或为空。")
    return value.strip()


def resolve_page_id(page_id_or_url: str) -> str:
    text = page_id_or_url.strip()
    if text.isdigit():
        return text

    parsed = urlparse(text)
    page_id = parse_qs(parsed.query).get("pageId", [None])[0]
    if page_id and page_id.isdigit():
        return page_id

    path_parts = [part for part in parsed.path.split("/") if part]
    if "pages" in path_parts:
        index = path_parts.index("pages")
        if index + 1 < len(path_parts) and path_parts[index + 1].isdigit():
            return path_parts[index + 1]

    raise SystemExit("无法从 `page_id_or_url` 解析 pageId。")


def sanitize_page_title(title: str) -> str:
    sanitized = "".join("_" if ch in INVALID_PATH_CHARS else ch for ch in title).strip()
    sanitized = sanitized.rstrip(". ")
    return sanitized or "untitled"


def find_confluence_command() -> List[str]:
    for candidate in ("confluence.cmd", "confluence"):
        path = shutil.which(candidate)
        if path:
            return [path]
    raise SystemExit("未找到 confluence-cli，请先确认 `confluence` 命令可用。")


def run_confluence(command: List[str]) -> str:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "未知错误"
        raise RuntimeError(message)
    return completed.stdout


def get_page_info(cli: List[str], page_id: str) -> Dict[str, object]:
    output = run_confluence(cli + ["info", page_id])
    match = TITLE_PATTERN.search(output)
    if not match:
        raise RuntimeError(f"无法解析页面标题: {page_id}")
    return {"title": match.group(1).strip()}


def get_page_tree(cli: List[str], root_page_id: str) -> List[Dict[str, Optional[str]]]:
    tree_output = run_confluence(cli + ["children", root_page_id, "--recursive", "--format", "json"])
    tree_data = json.loads(tree_output)

    pages: List[Dict[str, Optional[str]]] = []
    pages.append({"id": root_page_id, "title": None, "parentId": None})
    for child in tree_data.get("children", []):
        pages.append(
            {
                "id": str(child["id"]),
                "title": child.get("title"),
                "parentId": str(child.get("parentId")) if child.get("parentId") else None,
            }
        )
    return pages


def build_page_map(
    cli: List[str],
    root_page_id: str,
) -> Dict[str, Dict[str, Optional[str]]]:
    pages = get_page_tree(cli, root_page_id)
    page_map: Dict[str, Dict[str, Optional[str]]] = {}

    for page in pages:
        page_id = page["id"]
        if page["title"] is None:
            info = get_page_info(cli, page_id)
            title = str(info["title"])
        else:
            title = str(page["title"])

        page_map[page_id] = {
            "id": page_id,
            "title": title,
            "parentId": page["parentId"],
        }

    return page_map


def build_page_directory(
    page_id: str,
    page_map: Dict[str, Dict[str, Optional[str]]],
    download_root: Path,
    cache: Dict[str, Path],
) -> Path:
    if page_id in cache:
        return cache[page_id]

    page = page_map[page_id]
    name = sanitize_page_title(str(page["title"]))
    parent_id = page["parentId"]

    if parent_id:
        parent_dir = build_page_directory(parent_id, page_map, download_root, cache)
        path = parent_dir / name
    else:
        path = download_root / name

    cache[page_id] = path
    return path


def download_attachments_for_page(
    cli: List[str],
    page_id: str,
    target_dir: Path,
) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"confluence_{page_id}_") as temp_dir:
        temp_path = Path(temp_dir)
        run_confluence(cli + ["attachments", page_id, "--download", "--dest", str(temp_path)])

        for downloaded_file in temp_path.iterdir():
            if not downloaded_file.is_file():
                continue
            final_path = target_dir / downloaded_file.name
            if final_path.exists():
                final_path.unlink()
            shutil.move(str(downloaded_file), str(final_path))


def main() -> None:
    config = load_config()
    page_id_or_url = require_config_value(config, "page_id_or_url")
    download_root = Path(require_config_value(config, "download_root")).expanduser()

    cli = find_confluence_command()
    root_page_id = resolve_page_id(page_id_or_url)
    page_map = build_page_map(cli, root_page_id)

    directory_cache: Dict[str, Path] = {}
    page_items = list(page_map.values())
    total_pages = len(page_items)

    print(f"准备下载，共 {total_pages} 个页面。")
    print(f"下载根目录: {download_root}")

    for index, page in enumerate(page_items, start=1):
        page_id = str(page["id"])
        page_title = str(page["title"])
        target_dir = build_page_directory(page_id, page_map, download_root, directory_cache)
        print(f"[{index}/{total_pages}] 下载页面附件: {page_title}")
        print(f"  -> {target_dir}")
        try:
            download_attachments_for_page(cli, page_id, target_dir)
        except RuntimeError as exc:
            print(f"  下载失败: {exc}")

    print("下载完成。")


if __name__ == "__main__":
    main()
