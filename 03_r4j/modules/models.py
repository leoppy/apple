from __future__ import annotations

from dataclasses import dataclass
from typing import Set


@dataclass
class Requirement:
    key: str
    name: str
    level: str
    project_name: str
    project_id: int
    node_id: int
    parent_id: int | None = None
    description: str = ""


@dataclass
class TestCase:
    case_id: str
    case_name: str
    test_type: str
    traced_keys: Set[str]
    result: str
    source_file: str
    source_page: str


@dataclass
class TraceIssue:
    severity: str
    issue_type: str
    testcase_id: str
    requirement_key: str
    description: str
