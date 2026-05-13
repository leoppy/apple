import argparse
import json
import os
import re
from typing import Dict, List, Tuple


CUSTOM_KEYWORDS = [
    "你简历",
    "简历里",
    "某候选人",
    "该候选人",
    "朱艳玲",
    "张三",
    "李四",
    "王五",
]


def parse_frontmatter(text: str) -> Dict[str, str]:
    text = text.lstrip("\ufeff")
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, flags=re.S)
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


def extract_section(text: str, heading: str) -> str:
    text = text.lstrip("\ufeff")
    pattern = rf"^# {re.escape(heading)}\r?\n(.*?)(\r?\n# |\Z)"
    m = re.search(pattern, text, flags=re.S | re.M)
    if not m:
        return ""
    return m.group(1).strip()


def first_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def load_common_questions(bank_dir: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    for fn in sorted(os.listdir(bank_dir)):
        if not fn.endswith(".md"):
            continue
        path = os.path.join(bank_dir, fn)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        fm = parse_frontmatter(text)
        q = extract_section(text, "题目")
        a = extract_section(text, "参考答案")
        qid = fm.get("id", "")
        tags = parse_tags(fm.get("tags", ""))
        if not qid:
            qid = os.path.splitext(fn)[0]
        items.append(
            {
                "source": "common_bank",
                "kind": "通用",
                "id": qid,
                "tags": tags,
                "type": fm.get("type", ""),
                "difficulty": fm.get("difficulty", ""),
                "question": first_line(q),
                "answer": a,
                "file": path,
            }
        )
    return items


def maybe_customize_from_resume(resume_txt: str, count: int) -> List[Dict[str, str]]:
    if not resume_txt or not os.path.exists(resume_txt):
        return []
    with open(resume_txt, "r", encoding="utf-8") as f:
        raw = f.read()

    lower = raw.lower()
    hints = []
    if any(x in lower for x in ["pytest", "allure", "requests", "postman", "jmeter"]):
        hints.append(
            {
                "question": "请结合你做过的项目，讲一次你设计自动化回归策略的过程：如何分层、如何选冒烟集、如何保证结果可信？",
                "tags": ["项目深挖", "工程习惯", "测试工程"],
            }
        )
    if any(x in lower for x in ["bom", "neo4j", "mysql", "flask", "spring", "vue"]):
        hints.append(
            {
                "question": "针对一个包含多服务和多数据源的系统，你会如何设计端到端测试，确保关键业务链路与数据一致性？",
                "tags": ["场景题", "项目深挖", "测试工程"],
            }
        )
    if any(x in lower for x in ["需求", "评审", "跨部门", "缺陷", "上线"]):
        hints.append(
            {
                "question": "当测试结论与开发结论冲突时，你如何基于证据推进决策，并控制上线风险？",
                "tags": ["行为题", "跨部门协作", "场景题"],
            }
        )

    out: List[Dict[str, str]] = []
    for i, h in enumerate(hints[:count], start=1):
        out.append(
            {
                "source": "resume_custom",
                "kind": "定制（不入库）",
                "id": f"CUST{i:03d}",
                "tags": h["tags"],
                "type": "定制题",
                "difficulty": "按候选人画像",
                "question": h["question"],
                "answer": "面试官可在最终定稿阶段补充参考答案，或由模型生成。",
                "file": "N/A",
            }
        )

    return out


def pick_common(common: List[Dict[str, str]], tags: List[str], count: int) -> List[Dict[str, str]]:
    if count <= 0:
        return []
    if not tags:
        return common[:count]
    wanted = {t.strip() for t in tags if t.strip()}
    filtered = [q for q in common if wanted.intersection(set(q.get("tags", [])))]
    if len(filtered) >= count:
        return filtered[:count]
    used = {q["id"] for q in filtered}
    for q in common:
        if q["id"] in used:
            continue
        filtered.append(q)
        if len(filtered) >= count:
            break
    return filtered


def detect_custom_in_bank(common: List[Dict[str, str]]) -> List[str]:
    bad: List[str] = []
    for q in common:
        text = q.get("question", "")
        if any(k in text for k in CUSTOM_KEYWORDS):
            bad.append(f"{q.get('id', '')}:{os.path.basename(q.get('file', ''))}")
    return bad


def split_ratio(total: int, custom_ratio: int, common_ratio: int) -> Tuple[int, int]:
    if total <= 0:
        return 0, 0
    if custom_ratio <= 0 or common_ratio <= 0:
        return 0, total
    custom = round(total * custom_ratio / (custom_ratio + common_ratio))
    common = total - custom
    if custom < common:
        custom, common = common, custom
    return custom, common


def main() -> None:
    parser = argparse.ArgumentParser(description="生成候选题梗概（先选题，再定稿）")
    parser.add_argument("--candidate", required=True, help="候选人姓名")
    parser.add_argument("--total", type=int, default=6, help="候选题总数")
    parser.add_argument("--tags", default="", help="逗号分隔标签")
    parser.add_argument("--resume-txt", default="", help="简历文本路径（可选）")
    parser.add_argument("--ratio", default="2:1", help="定制:通用 比例，默认2:1")
    parser.add_argument("--bank-dir", default=os.path.join("question_bank", "common"), help="通用题库目录")
    parser.add_argument("--output-dir", default="outputs", help="输出目录")
    args = parser.parse_args()

    tags = [x.strip() for x in args.tags.split(",") if x.strip()]

    try:
        c_ratio, g_ratio = [int(x) for x in args.ratio.split(":", 1)]
    except Exception as exc:
        raise ValueError("--ratio 格式错误，应为 a:b，例如 2:1") from exc

    common_pool = load_common_questions(args.bank_dir)
    custom_n, common_n = split_ratio(args.total, c_ratio, g_ratio)

    custom_candidates = maybe_customize_from_resume(args.resume_txt, custom_n)
    if len(custom_candidates) < custom_n:
        common_n += (custom_n - len(custom_candidates))

    common_candidates = pick_common(common_pool, tags, common_n)
    merged = custom_candidates + common_candidates

    bad = detect_custom_in_bank(common_pool)

    os.makedirs(args.output_dir, exist_ok=True)
    outline_md = os.path.join(args.output_dir, f"{args.candidate}_候选题梗概.md")
    outline_json = os.path.join(args.output_dir, f"{args.candidate}_候选题梗概.json")

    serial_items = []
    for i, q in enumerate(merged, start=1):
        row = dict(q)
        row["index"] = i
        serial_items.append(row)

    data = {
        "candidate": args.candidate,
        "total": len(serial_items),
        "ratio": args.ratio,
        "notes": {
            "custom_in_bank_violations": bad,
            "rule": "定制题不入库；仅作为当次输出候选题",
        },
        "items": serial_items,
    }

    with open(outline_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(outline_md, "w", encoding="utf-8") as f:
        f.write(f"# {args.candidate} 候选题梗概\n\n")
        f.write(f"- 总数：{len(serial_items)}\n")
        f.write(f"- 配比（定制:通用）：{args.ratio}\n")
        f.write("- 说明：先选题，再生成最终面试题文档\n\n")

        if bad:
            f.write("## 题库合规预警\n")
            f.write("以下题目疑似含定制痕迹，请先修正再入库使用：\n")
            for b in bad:
                f.write(f"- {b}\n")
            f.write("\n")

        f.write("## 候选题清单\n")
        for q in serial_items:
            f.write(f"### [{q['index']}] {q['question']}\n")
            f.write(f"- 类型标识：{q['kind']}\n")
            f.write(f"- 题号：{q['id']}\n")
            f.write(f"- 标签：{', '.join(q.get('tags', []))}\n")
            f.write(f"- 来源：{q['source']}\n\n")

        f.write("## 面试官选择\n")
        f.write("请回复要保留的题号（例如：1,2,4）。确认后再生成最终题单。\n")

    print(outline_md)
    print(outline_json)


if __name__ == "__main__":
    main()
