from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set

from .models import Requirement, TestCase, TraceIssue


class Tracer:
    def __init__(self, v_model_mapping: Dict[str, str]):
        self.v_model_mapping = v_model_mapping

    def run_full_check(self, testcases: List[TestCase], requirements: Dict[str, Requirement]) -> List[TraceIssue]:
        issues: List[TraceIssue] = []
        issues.extend(self.check_orphan_traces(testcases, requirements))
        issues.extend(self.check_missing_coverage(testcases, requirements))
        issues.extend(self.check_v_model_consistency(testcases, requirements))
        return issues

    def check_orphan_traces(self, testcases: List[TestCase], requirements: Dict[str, Requirement]) -> List[TraceIssue]:
        issues: List[TraceIssue] = []
        for tc in testcases:
            for key in tc.traced_keys:
                if key not in requirements:
                    issues.append(
                        TraceIssue(
                            severity="high",
                            issue_type="orphan",
                            testcase_id=tc.case_id,
                            requirement_key=key,
                            description=f"追溯需求不存在: {key}",
                            components="",
                        )
                    )
        return issues

    def check_missing_coverage(self, testcases: List[TestCase], requirements: Dict[str, Requirement]) -> List[TraceIssue]:
        covered: Set[str] = set()
        for tc in testcases:
            covered.update(key for key in tc.traced_keys if key in requirements)

        issues: List[TraceIssue] = []
        for key, req in requirements.items():
            if key not in covered:
                issues.append(
                    TraceIssue(
                        severity="medium",
                        issue_type="missing",
                        testcase_id="-",
                        requirement_key=key,
                        description=f"需求未被覆盖: {req.name}",
                        components=req.components,
                    )
                )
        return issues

    def check_v_model_consistency(self, testcases: List[TestCase], requirements: Dict[str, Requirement]) -> List[TraceIssue]:
        issues: List[TraceIssue] = []
        for tc in testcases:
            expected_level = self.v_model_mapping.get(tc.test_type)
            if not expected_level:
                continue
            for key in tc.traced_keys:
                req = requirements.get(key)
                if not req:
                    continue
                if req.level != expected_level:
                    issues.append(
                        TraceIssue(
                            severity="low",
                            issue_type="mismatch",
                            testcase_id=tc.case_id,
                            requirement_key=key,
                            description=f"测试类型 {tc.test_type} 期望追溯 {expected_level}，实际为 {req.level}",
                            components=req.components,
                        )
                    )
        return issues

    @staticmethod
    def issue_summary(issues: List[TraceIssue]) -> Dict[str, int]:
        summary = defaultdict(int)
        for issue in issues:
            summary[issue.issue_type] += 1
        return dict(summary)
