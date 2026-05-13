import argparse
import os
import re
from typing import List, Tuple


BLOCK_PATTERNS = [
    r"^candidate:\s*",
    r"你简历",
    r"简历里",
    r"某候选人",
    r"该候选人",
    r"朱艳玲",
    r"张三",
    r"李四",
    r"王五",
]


def scan_file(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().lstrip("\ufeff")
    hits = []
    for p in BLOCK_PATTERNS:
        if re.search(p, text, flags=re.M):
            hits.append(p)
    return hits


def main() -> None:
    parser = argparse.ArgumentParser(description="检查通用题库是否混入定制题痕迹")
    parser.add_argument("--bank-dir", default=os.path.join("question_bank", "common"))
    args = parser.parse_args()

    if not os.path.isdir(args.bank_dir):
        raise FileNotFoundError(args.bank_dir)

    violations: List[Tuple[str, List[str]]] = []
    for fn in sorted(os.listdir(args.bank_dir)):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(args.bank_dir, fn)
        hits = scan_file(p)
        if hits:
            violations.append((fn, hits))

    if not violations:
        print("PASS: 通用题库未发现定制题痕迹")
        return

    print("FAIL: 检测到疑似定制题痕迹")
    for fn, hits in violations:
        print(f"- {fn}: {', '.join(hits)}")
    raise SystemExit(2)


if __name__ == "__main__":
    main()
