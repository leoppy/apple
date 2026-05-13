import argparse
import json
import os
from typing import Dict, List


def parse_pick(pick: str) -> List[int]:
    out: List[int] = []
    for x in pick.split(","):
        x = x.strip()
        if not x:
            continue
        out.append(int(x))
    return out


def load_common_question_by_id(bank_dir: str, qid: str) -> str:
    qid = qid.strip()
    for fn in sorted(os.listdir(bank_dir)):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(bank_dir, fn)
        with open(p, "r", encoding="utf-8") as f:
            txt = f.read().lstrip("\ufeff")
        if f"id: {qid}" in txt:
            return txt
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="根据面试官选题号生成最终面试题文档")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--outline-json", required=True)
    parser.add_argument("--pick", required=True, help="例如 1,2,4")
    parser.add_argument("--bank-dir", default=os.path.join("question_bank", "common"))
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument(
        "--allow-mismatch-final-count",
        action="store_true",
        help="允许最终选题数量与最终题量目标不一致（默认严格校验）",
    )
    args = parser.parse_args()

    with open(args.outline_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    picks = set(parse_pick(args.pick))
    items: List[Dict] = data.get("items", [])
    chosen = [it for it in items if int(it.get("index", -1)) in picks]
    final_target_total = int(data.get("final_target_total", 0))

    if (not args.allow_mismatch_final_count) and final_target_total > 0 and len(chosen) != final_target_total:
        raise ValueError(
            f"最终选题数量不匹配：目标 {final_target_total}，当前 {len(chosen)}。"
            "如需放宽，请追加 --allow-mismatch-final-count"
        )

    os.makedirs(args.output_dir, exist_ok=True)
    out_path = os.path.join(args.output_dir, f"{args.candidate}_面试题.md")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {args.candidate} 面试题\n\n")
        f.write("## 选题信息\n")
        f.write(f"- 候选清单：{os.path.basename(args.outline_json)}\n")
        f.write(f"- 已选题号：{args.pick}\n")
        f.write(f"- 最终题量目标：{final_target_total}\n")
        f.write(f"- 实际选题数量：{len(chosen)}\n")
        f.write(f"- 严格数量校验：{'否（已放宽）' if args.allow_mismatch_final_count else '是'}\n\n")

        f.write("## 最终题目\n")
        qn = 1
        for it in chosen:
            kind = it.get("kind", "")
            qid = it.get("id", "")
            q = it.get("question", "")
            tags = ", ".join(it.get("tags", []))

            f.write(f"### Q{qn}（{qid}）\n")
            f.write(f"- 类型标识：{kind}\n")
            f.write(f"- 标签：{tags}\n")
            f.write(f"- 题目：{q}\n")

            if kind.startswith("通用"):
                full = load_common_question_by_id(args.bank_dir, qid)
                if full:
                    f.write("\n")
                    f.write(full)
                    f.write("\n")
                else:
                    f.write("- 参考答案：题库检索失败，请人工补充。\n")
                    f.write("- 追问：请围绕该题考察点继续展开。\n")
            else:
                f.write("- 参考答案：定制题（不入库），建议结合岗位要求现场追问。\n")
                f.write("- 追问：请要求候选人给出真实项目证据与可量化结果。\n")

            f.write("\n")
            qn += 1

    print(out_path)


if __name__ == "__main__":
    main()
