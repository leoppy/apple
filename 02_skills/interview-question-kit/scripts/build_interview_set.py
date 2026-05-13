import argparse
import os
import re
from typing import List, Dict


def parse_frontmatter(text: str) -> Dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if not m:
        return {}
    block = m.group(1)
    result: Dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        result[k.strip()] = v.strip()
    return result


def parse_tags(value: str) -> List[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        raw = value[1:-1]
        return [x.strip().strip('"').strip("'") for x in raw.split(",") if x.strip()]
    return [value] if value else []


def load_questions(bank_dir: str) -> List[Dict[str, str]]:
    questions = []
    for fn in sorted(os.listdir(bank_dir)):
        if not fn.endswith(".md"):
            continue
        path = os.path.join(bank_dir, fn)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        fm = parse_frontmatter(text)
        tags = parse_tags(fm.get("tags", ""))
        questions.append({"file": path, "text": text, "id": fm.get("id", ""), "tags": tags})
    return questions


def filter_questions(questions: List[Dict[str, str]], wanted_tags: List[str]) -> List[Dict[str, str]]:
    if not wanted_tags:
        return questions
    wanted = {t.strip() for t in wanted_tags if t.strip()}
    return [q for q in questions if wanted.intersection(set(q["tags"]))]


def extract_title(q_text: str) -> str:
    for line in q_text.splitlines():
        if line.startswith("# 题目"):
            continue
        if line.strip() and not line.startswith("---") and not line.startswith("id:") and not line.startswith("tags:") and not line.startswith("type:") and not line.startswith("difficulty:"):
            return line.strip()
    return "（未命名题目）"


def main() -> None:
    parser = argparse.ArgumentParser(description="按标签从题库生成候选人面试题单")
    parser.add_argument("--candidate", required=True, help="候选人姓名")
    parser.add_argument("--tags", default="", help="逗号分隔标签，例如 项目深挖,行为题")
    parser.add_argument("--count", type=int, default=5, help="题目数量")
    parser.add_argument("--bank-dir", default=os.path.join("question_bank", "common"), help="题库目录")
    parser.add_argument("--output-dir", default="outputs", help="输出目录")
    args = parser.parse_args()

    questions = load_questions(args.bank_dir)
    wanted_tags = [x.strip() for x in args.tags.split(",")] if args.tags else []
    selected = filter_questions(questions, wanted_tags)[: args.count]

    os.makedirs(args.output_dir, exist_ok=True)
    out_path = os.path.join(args.output_dir, f"{args.candidate}_面试题.md")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {args.candidate} 面试题\n\n")
        f.write(f"- 标签筛选：{', '.join(wanted_tags) if wanted_tags else '无（全量）'}\n")
        f.write(f"- 题目数量：{len(selected)}\n\n")
        for i, q in enumerate(selected, start=1):
            f.write(f"## Q{i}（{q['id']}）\n")
            f.write(f"- 来源：{os.path.basename(q['file'])}\n")
            f.write(f"- 标签：{', '.join(q['tags'])}\n")
            f.write(f"- 题干：{extract_title(q['text'])}\n\n")
            f.write(q["text"])
            f.write("\n\n")

    print(out_path)


if __name__ == "__main__":
    main()
