from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .models import Requirement, TestCase, TraceIssue


class ReportGenerator:
    def __init__(
        self,
        output_cfg: Dict,
        project_root: Path,
        testcases: List[TestCase],
        requirements: Dict[str, Requirement],
        issues: List[TraceIssue],
        coverage_rows: List[Dict],
        pass_rate_rows: List[Dict],
    ):
        self.output_cfg = output_cfg
        self.project_root = project_root.resolve()
        self.testcases = testcases
        self.requirements = requirements
        self.issues = issues
        self.coverage_rows = coverage_rows
        self.pass_rate_rows = pass_rate_rows
        self.issue_index = self._build_issue_index(issues)

    @staticmethod
    def _build_issue_index(issues: List[TraceIssue]) -> Dict[tuple[str, str], List[TraceIssue]]:
        index: Dict[tuple[str, str], List[TraceIssue]] = {}
        for issue in issues:
            key = (issue.testcase_id, issue.requirement_key)
            index.setdefault(key, []).append(issue)
        return index

    def generate_report(self, output_filename: str | None = None) -> Path:
        date_dir = datetime.now().strftime("%Y%m%d")
        output_dir = self.project_root / "tempFile" / "reports" / date_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        if output_filename:
            filename = output_filename
        else:
            template = self.output_cfg.get("filename_template", "v_model_trace_report_{timestamp}.xlsx")
            filename = template.format(timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"))
        output_path = output_dir / filename

        wb = Workbook()
        wb.remove(wb.active)
        self.create_trace_matrix_sheet(wb)
        self.create_coverage_sheet(wb)
        self.create_issues_sheet(wb)
        self.create_pass_rate_sheet(wb)
        wb.save(output_path)
        return output_path

    def create_trace_matrix_sheet(self, wb: Workbook) -> None:
        ws = wb.create_sheet("追溯矩阵")
        headers = ["用例ID", "用例名称", "测试类型", "追溯需求", "测试结果", "来源文件", "Confluence页面"]
        ws.append(headers)

        orphan_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        mismatch_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
        for tc in self.testcases:
            keys = sorted(tc.traced_keys) if tc.traced_keys else ["-"]
            for key in keys:
                row = [tc.case_id, tc.case_name, tc.test_type, key, tc.result, tc.source_file, tc.source_page]
                ws.append(row)
                row_num = ws.max_row
                issue_list = self.issue_index.get((tc.case_id, key), [])
                issue_types = {issue.issue_type for issue in issue_list}
                if "orphan" in issue_types:
                    for c in range(1, len(headers) + 1):
                        ws.cell(row=row_num, column=c).fill = orphan_fill
                elif "mismatch" in issue_types:
                    for c in range(1, len(headers) + 1):
                        ws.cell(row=row_num, column=c).fill = mismatch_fill

        self._format_sheet(ws)

    def create_coverage_sheet(self, wb: Workbook) -> None:
        ws = wb.create_sheet("覆盖率统计")
        headers = ["项目", "层级", "总需求数", "已覆盖数", "未覆盖数", "覆盖率"]
        ws.append(headers)
        for row in self.coverage_rows:
            ws.append(
                [
                    row["project"],
                    row["level"],
                    row["total_requirements"],
                    row["covered_requirements"],
                    row["uncovered_requirements"],
                    row["coverage_rate"],
                ]
            )
        self._format_sheet(ws, percentage_columns={6})

    def create_issues_sheet(self, wb: Workbook) -> None:
        ws = wb.create_sheet("问题清单")
        headers = ["严重性", "问题类型", "用例ID", "需求Key", "问题描述"]
        ws.append(headers)
        severity_order = {"high": 0, "medium": 1, "low": 2}
        sorted_issues = sorted(self.issues, key=lambda x: severity_order.get(x.severity, 99))
        for issue in sorted_issues:
            ws.append([issue.severity, issue.issue_type, issue.testcase_id, issue.requirement_key, issue.description])
        self._format_sheet(ws)

    def create_pass_rate_sheet(self, wb: Workbook) -> None:
        ws = wb.create_sheet("通过率统计")
        headers = ["测试类型", "总用例数", "通过", "失败", "未执行", "通过率"]
        ws.append(headers)
        for row in self.pass_rate_rows:
            ws.append(
                [
                    row["test_type"],
                    row["total"],
                    row["passed"],
                    row["failed"],
                    row["not_executed"],
                    row["pass_rate"],
                ]
            )
        self._format_sheet(ws, percentage_columns={6})

    @staticmethod
    def _format_sheet(ws, percentage_columns: set[int] | None = None) -> None:
        percentage_columns = percentage_columns or set()
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        for col in range(1, ws.max_column + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for col in range(1, ws.max_column + 1):
            max_len = 0
            for row in range(1, ws.max_row + 1):
                value = ws.cell(row=row, column=col).value
                if value is None:
                    continue
                max_len = max(max_len, len(str(value)))
            ws.column_dimensions[get_column_letter(col)].width = min(max(max_len + 2, 10), 60)

        for row in range(2, ws.max_row + 1):
            for col in percentage_columns:
                cell = ws.cell(row=row, column=col)
                cell.number_format = "0.00%"
        ws.freeze_panes = "A2"
