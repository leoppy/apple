from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from .models import Requirement, TestCase


class CoverageAnalyzer:
    def __init__(self, requirements: Dict[str, Requirement], testcases: List[TestCase]):
        self.requirements = requirements
        self.testcases = testcases

    def calculate_requirement_coverage(self) -> tuple[List[Dict], List[Dict]]:
        """计算需求覆盖率，返回 (详细数据, 汇总数据)"""
        covered_keys = set()
        for tc in self.testcases:
            covered_keys.update(k for k in tc.traced_keys if k in self.requirements)

        # 生成详细的需求覆盖率数据（每个需求一行）
        detail_rows: List[Dict] = []
        for req in self.requirements.values():
            is_covered = req.key in covered_keys
            detail_rows.append(
                {
                    "requirement_key": req.key,
                    "module": req.module,
                    "components": req.components,
                    "issue_type": req.issue_type,
                    "labels": req.labels,
                    "priority": req.priority,
                    "is_covered": "是" if is_covered else "否",
                }
            )

        # 生成汇总数据
        grouped: Dict[tuple[str, str], List[Dict]] = defaultdict(list)
        for req in self.requirements.values():
            is_covered = req.key in covered_keys
            grouped[(req.project_name, req.level)].append({"is_covered": is_covered})

        summary_rows: List[Dict] = []
        for (project_name, level), group_data in sorted(grouped.items()):
            total = len(group_data)
            covered = sum(1 for item in group_data if item["is_covered"])
            uncovered = total - covered
            coverage = (covered / total) if total else 0.0
            summary_rows.append(
                {
                    "project": project_name,
                    "level": level,
                    "total_requirements": total,
                    "covered_requirements": covered,
                    "uncovered_requirements": uncovered,
                    "coverage_rate": coverage,
                }
            )

        return detail_rows, summary_rows

    def calculate_orphan_traces(self) -> List[Dict]:
        """统计孤立追溯：测试用例追溯了不存在的需求"""
        orphan_traces: Dict[str, Dict] = defaultdict(lambda: {"case_ids": [], "modules": set()})

        for tc in self.testcases:
            for key in tc.traced_keys:
                if key not in self.requirements:
                    orphan_traces[key]["case_ids"].append(tc.case_id)
                    if tc.module:
                        orphan_traces[key]["modules"].add(tc.module)

        rows: List[Dict] = []
        for req_key, data in sorted(orphan_traces.items()):
            case_ids = data["case_ids"]
            modules = data["modules"]
            rows.append(
                {
                    "requirement_key": req_key,
                    "testcase_count": len(case_ids),
                    "testcase_ids": ", ".join(sorted(case_ids)),
                    "modules": ", ".join(sorted(modules)) if modules else "",
                }
            )

        return rows

    def calculate_test_pass_rate(self) -> List[Dict]:
        # 按模块分组统计
        grouped: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0, "not_executed": 0})
        for tc in self.testcases:
            module = tc.module if tc.module else "未分类"
            bucket = grouped[module]
            bucket["total"] += 1
            bucket[tc.result] = bucket.get(tc.result, 0) + 1

        rows: List[Dict] = []
        total_total = total_passed = total_failed = total_not_executed = 0
        for module, stat in sorted(grouped.items(), key=lambda x: x[0]):
            passed = stat.get("passed", 0)
            failed = stat.get("failed", 0)
            not_executed = stat.get("not_executed", 0)
            denominator = passed + failed
            pass_rate = (passed / denominator) if denominator else 0.0
            rows.append(
                {
                    "module": module,
                    "total": stat.get("total", 0),
                    "passed": passed,
                    "failed": failed,
                    "not_executed": not_executed,
                    "pass_rate": pass_rate,
                }
            )
            total_total += stat.get("total", 0)
            total_passed += passed
            total_failed += failed
            total_not_executed += not_executed

        # 添加汇总行
        denominator = total_passed + total_failed
        total_pass_rate = (total_passed / denominator) if denominator else 0.0
        rows.append(
            {
                "module": "TOTAL",
                "total": total_total,
                "passed": total_passed,
                "failed": total_failed,
                "not_executed": total_not_executed,
                "pass_rate": total_pass_rate,
            }
        )
        return rows

    def calculate_module_overview(self) -> List[Dict]:
        """统计每个模块的未覆盖需求数量"""
        covered_keys = set()
        for tc in self.testcases:
            covered_keys.update(k for k in tc.traced_keys if k in self.requirements)

        # 按模块统计未覆盖需求
        module_stats: Dict[str, Dict] = defaultdict(lambda: {"uncovered_keys": set()})

        for req in self.requirements.values():
            is_covered = req.key in covered_keys
            if not is_covered and req.components:
                # 拆分 components 字段（可能包含多个模块，逗号分隔）
                modules = [m.strip() for m in req.components.split(",") if m.strip()]
                for module in modules:
                    module_stats[module]["uncovered_keys"].add(req.key)

        # 生成统计行
        rows: List[Dict] = []
        for module, stats in sorted(module_stats.items()):
            uncovered_count = len(stats["uncovered_keys"])
            rows.append(
                {
                    "module": module,
                    "uncovered_count": uncovered_count,
                    "uncovered_keys": ", ".join(sorted(stats["uncovered_keys"])),
                }
            )

        return rows
