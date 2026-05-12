from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Set

from openpyxl import load_workbook

from .confluence_client import ConfluenceClient
from .models import TestCase

ISSUE_KEY_PATTERN = re.compile(r"[A-Z]+-\d+")


class TestCaseLoader:
    def __init__(self, config: Dict, client: ConfluenceClient, use_cache: bool = True):
        self.config = config
        self.client = client
        self.use_cache = use_cache
        cache_cfg = config.get("cache", {})
        self.cache_enabled = bool(cache_cfg.get("enabled", True)) and use_cache
        self.cache_dir = Path(cache_cfg.get("dir", "tempFile/cache"))
        self.cache_ttl_hours = int(cache_cfg.get("ttl_hours", 24))

    def load_all_testcases(self) -> List[TestCase]:
        all_cases: List[TestCase] = []
        for tc_cfg in self.config.get("confluence_testcases", []):
            all_cases.extend(self._load_from_page_config(tc_cfg))
        return all_cases

    def _load_from_page_config(self, tc_cfg: Dict) -> List[TestCase]:
        page_id = str(tc_cfg["page_id"])
        root_page = self.client.get_page(page_id)
        pages = [root_page]
        if tc_cfg.get("traverse_children", False):
            pages.extend(self.client.get_descendant_pages(page_id))

        cases: List[TestCase] = []
        for page in pages:
            current_page_id = str(page["id"])
            current_page_title = page.get("title", "")
            attachments = self.client.get_page_attachments(current_page_id)
            excel_attachments = [
                item
                for item in attachments
                if str(item.get("title", "")).lower().endswith((".xlsx", ".xlsm", ".xls"))
            ]

            for attachment in excel_attachments:
                excel_path = self._get_excel_file(current_page_id, attachment)
                cases.extend(
                    self.parse_excel(
                        excel_path=excel_path,
                        config=tc_cfg,
                        source_page=current_page_title,
                    )
                )
        return cases

    def _get_excel_file(self, page_id: str, attachment: Dict) -> Path:
        attachment_id = str(attachment.get("id"))
        attachment_version = str(attachment.get("version", {}).get("number", "0"))
        attachment_name = str(attachment.get("title", "attachment.xlsx"))
        safe_name = attachment_name.replace("\\", "_").replace("/", "_")
        cached_name = f"testcases_{page_id}_{attachment_id}_{attachment_version}_{safe_name}"
        cache_file = self.cache_dir / cached_name

        if self.cache_enabled and cache_file.exists():
            age_seconds = time.time() - cache_file.stat().st_mtime
            if age_seconds <= self.cache_ttl_hours * 3600:
                return cache_file

        downloaded = self.client.download_attachment(attachment=attachment, save_path=cache_file)
        return downloaded

    def parse_excel(self, excel_path: Path, config: Dict, source_page: str) -> List[TestCase]:
        wb = load_workbook(excel_path, data_only=True, read_only=True)
        sheet_pattern = re.compile(config.get("sheet_pattern", ".*测试用例.*"))
        excel_columns = config.get("excel_columns", {})
        result_mapping = config.get("result_mapping", {})
        test_type = str(config.get("test_type", "")).strip()

        testcases: List[TestCase] = []
        for sheet_name in wb.sheetnames:
            if not sheet_pattern.search(sheet_name):
                continue
            ws = wb[sheet_name]
            rows = ws.iter_rows(values_only=True)
            try:
                header_row = next(rows)
            except StopIteration:
                continue
            if not header_row:
                continue

            header_map = {str(v).strip(): idx for idx, v in enumerate(header_row) if v is not None}
            id_col = header_map.get(str(excel_columns.get("id", "")).strip())
            name_col = header_map.get(str(excel_columns.get("name", "")).strip())
            trace_col = header_map.get(str(excel_columns.get("trace", "")).strip())
            result_col = header_map.get(str(excel_columns.get("result", "")).strip())
            if id_col is None or trace_col is None:
                continue

            for row in rows:
                case_id = self._safe_cell(row, id_col)
                if not case_id:
                    continue
                case_name = self._safe_cell(row, name_col) if name_col is not None else ""
                trace_raw = self._safe_cell(row, trace_col)
                result_raw = self._safe_cell(row, result_col) if result_col is not None else ""
                traced_keys = self.extract_traced_keys(trace_raw)
                mapped_result = self._map_result(result_raw, result_mapping)
                testcases.append(
                    TestCase(
                        case_id=case_id,
                        case_name=case_name,
                        test_type=test_type,
                        traced_keys=traced_keys,
                        result=mapped_result,
                        source_file=excel_path.name,
                        source_page=source_page,
                    )
                )
        wb.close()
        return testcases

    @staticmethod
    def _safe_cell(row: tuple, col_idx: int | None) -> str:
        if col_idx is None or col_idx >= len(row):
            return ""
        value = row[col_idx]
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def extract_traced_keys(trace_cell_value: str) -> Set[str]:
        if not trace_cell_value:
            return set()
        keys = ISSUE_KEY_PATTERN.findall(trace_cell_value.upper())
        return set(keys)

    @staticmethod
    def _map_result(result_raw: str, mapping: Dict) -> str:
        value = str(result_raw or "").strip()
        if not value:
            return "not_executed"
        for target in ("passed", "failed", "not_executed"):
            candidates = {str(v).strip() for v in mapping.get(target, [])}
            if value in candidates:
                return target
        normalized = value.lower()
        if normalized in {"pass", "passed", "ok"}:
            return "passed"
        if normalized in {"fail", "failed", "ng"}:
            return "failed"
        return "not_executed"

    def dump_testcase_cache(self, testcases: List[TestCase]) -> Path:
        cache_file = self.cache_dir / "testcases_snapshot.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "case_id": tc.case_id,
                "case_name": tc.case_name,
                "test_type": tc.test_type,
                "traced_keys": sorted(tc.traced_keys),
                "result": tc.result,
                "source_file": tc.source_file,
                "source_page": tc.source_page,
            }
            for tc in testcases
        ]
        cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return cache_file
