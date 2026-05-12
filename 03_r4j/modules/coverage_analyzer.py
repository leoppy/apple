from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from .models import Requirement, TestCase


class CoverageAnalyzer:
    def __init__(self, requirements: Dict[str, Requirement], testcases: List[TestCase]):
        self.requirements = requirements
        self.testcases = testcases

    def calculate_requirement_coverage(self) -> List[Dict]:
        covered_keys = set()
        for tc in self.testcases:
            covered_keys.update(k for k in tc.traced_keys if k in self.requirements)

        grouped: Dict[tuple[str, str], List[Requirement]] = defaultdict(list)
        for req in self.requirements.values():
            grouped[(req.project_name, req.level)].append(req)

        rows: List[Dict] = []
        for (project_name, level), reqs in grouped.items():
            total = len(reqs)
            covered = sum(1 for req in reqs if req.key in covered_keys)
            uncovered = total - covered
            coverage = (covered / total) if total else 0.0
            rows.append(
                {
                    "project": project_name,
                    "level": level,
                    "total_requirements": total,
                    "covered_requirements": covered,
                    "uncovered_requirements": uncovered,
                    "coverage_rate": coverage,
                }
            )
        rows.sort(key=lambda x: (x["project"], x["level"]))
        return rows

    def calculate_test_pass_rate(self) -> List[Dict]:
        grouped: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0, "not_executed": 0})
        for tc in self.testcases:
            bucket = grouped[tc.test_type]
            bucket["total"] += 1
            bucket[tc.result] = bucket.get(tc.result, 0) + 1

        rows: List[Dict] = []
        total_total = total_passed = total_failed = total_not_executed = 0
        for test_type, stat in sorted(grouped.items(), key=lambda x: x[0]):
            passed = stat.get("passed", 0)
            failed = stat.get("failed", 0)
            not_executed = stat.get("not_executed", 0)
            denominator = passed + failed
            pass_rate = (passed / denominator) if denominator else 0.0
            rows.append(
                {
                    "test_type": test_type,
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

        denominator = total_passed + total_failed
        total_pass_rate = (total_passed / denominator) if denominator else 0.0
        rows.append(
            {
                "test_type": "TOTAL",
                "total": total_total,
                "passed": total_passed,
                "failed": total_failed,
                "not_executed": total_not_executed,
                "pass_rate": total_pass_rate,
            }
        )
        return rows
