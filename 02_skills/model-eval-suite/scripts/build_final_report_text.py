#!/usr/bin/env python3
"""生成本批次评测报告（纯文字版 - 无图片引用）"""

import os
from datetime import datetime

OUT = r'D:\01_github\banana\apple\02_skills\model-eval-suite\03_results'

# ============================================================
# 本批次评测结果数据
# ============================================================

SCORES = {
    "DQX6D": {
        "name": "queen",
        "JWNK6P": {"req": 4, "code": 3, "trace": 1, "note": "多模块架构清晰，CLI对齐，缺token-manager .env路径"},
        "TRW23D": {"req": 4, "code": 3, "trace": 1, "note": "功能完整，SSH查重用字符串比较有误判风险"},
        "GO7Q83": {"req": 3, "code": 2, "trace": 1, "note": "分类规则粗糙，else全归ROM，.data未双重记录"},
    },
    "I2QS4": {
        "name": "bishop",
        "JWNK6P": {"req": 4, "code": 3, "trace": 1, "note": "core/包结构优雅，TraceAnalyzer设计好，.env路径稍偏"},
        "TRW23D": {"req": 4, "code": 2, "trace": 1, "note": "结构清晰可扩展，check_git干跑下有小逻辑问题"},
        "GO7Q83": {"req": 4, "code": 3, "trace": 1, "note": "SectionInfo类含BOTH分类，.data双重记录处理正确"},
    },
    "KVAZ2": {
        "name": "rook",
        "JWNK6P": {"req": 5, "code": 3, "trace": 1, "note": "最完整模块化分包，BaseApiClient抽象，CLI全覆盖"},
        "TRW23D": {"req": 5, "code": 3, "trace": 1, "note": "_api_request通用层，指纹级查重，设计最好"},
        "GO7Q83": {"req": 5, "code": 3, "trace": 1, "note": "正则pattern数组，5张输出表，Top30模块，工程级质量"},
    },
    "9CNZI": {
        "name": "knight",
        "JWNK6P": {"req": 5, "code": 2, "trace": 1, "note": "单文件全能，.env路径精确指向token-manager"},
        "TRW23D": {"req": 4, "code": 3, "trace": 1, "note": "功能完整，GitLab缺422已存在处理分支"},
        "GO7Q83": {"req": 5, "code": 3, "trace": 1, "note": "Image Summary专解析，BOTH类型，SecOffs fallback"},
    },
}

TASKS = {
    "JWNK6P": "V模型需求-测试追溯统计工具",
    "TRW23D": "Git环境快速配置工具",
    "GO7Q83": "MAP文件内存解析工具",
}

# 人话总结
HUMAN_SUMMARY = {
    "JWNK6P": "V模型追溯功能都跑起来了，但各模型集成方式差异大，有用分包有用单文件，.env路径没对齐是共性问题。",
    "TRW23D": "Git配置功能完整，别名和SSH都到位，多数模型用了.env加载。但KVAZ2的指纹查重明显比其他模型严谨。",
    "GO7Q83": "MAP解析差距明显，KVAZ2和9CNZI输出5张表质量最好，DQX6D的分类规则太糙，整体嵌入式内存理解参差不齐。",
}


def score_color(total):
    if total >= 8:
        return "#059669", "#d1fae5"
    elif total >= 6:
        return "#d97706", "#fef3c7"
    else:
        return "#dc2626", "#fee2e2"


def build_html():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    model_avgs = {}
    for model, data in SCORES.items():
        totals = [data[t]["req"] + data[t]["code"] + data[t]["trace"] for t in TASKS]
        model_avgs[model] = sum(totals) / len(totals)

    ranked = sorted(SCORES.keys(), key=lambda m: model_avgs[m], reverse=True)
    medals = ["🥇", "🥈", "🥉", "4️⃣"]

    # 排名表
    rank_rows = ""
    for i, model in enumerate(ranked):
        data = SCORES[model]
        avg = model_avgs[model]
        fg, bg = score_color(avg)
        cells = ""
        for task in TASKS:
            td = data[task]
            total = td["req"] + td["code"] + td["trace"]
            tfg, tbg = score_color(total)
            cells += f'<td><span style="color:{tfg};font-weight:700;">{total}</span></td>'
        rank_rows += f"""
        <tr>
            <td>{medals[i]}</td>
            <td><strong>{model}</strong></td>
            <td style="color:#888;">{data['name']}</td>
            {cells}
            <td><strong style="color:{fg};">{avg:.1f}</strong></td>
        </tr>"""

    # 纯文字任务卡片（无图片引用）
    model_cards = ""
    for model in ranked:
        data = SCORES[model]
        avg = model_avgs[model]
        fg, bg = score_color(avg)
        task_rows = ""
        for task, task_name in TASKS.items():
            td = data[task]
            total = td["req"] + td["code"] + td["trace"]
            tfg, tbg = score_color(total)
            task_rows += f"""
            <div class="task-row">
                <div class="task-title">{task} / {task_name}</div>
                <div class="task-score">
                    <span class="badge" style="color:{tfg};background:{tbg};">{total}/10</span>
                    <span class="badge-sm">需求 {td['req']}/5 + 代码 {td['code']}/3 + 轨迹 {td['trace']}/2</span>
                </div>
                <div class="task-note">{td['note']}</div>
            </div>"""
        model_cards += f"""
        <div class="model-card">
            <div class="model-header">
                <div>
                    <span class="model-id">{model}</span>
                    <span class="model-name">({data['name']})</span>
                </div>
                <div class="avg-badge" style="color:{fg};background:{bg};">均 {avg:.1f}</div>
            </div>
            {task_rows}
            <div class="human-summary">{HUMAN_SUMMARY['JWNK6P']}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>评测报告 – 本批次（纯文字版）</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Microsoft YaHei','Segoe UI',sans-serif;background:#f0f2f5;color:#2b2d42;line-height:1.6}}
.hd{{background:linear-gradient(135deg,#1a1a2e,#0f3460);color:#fff;padding:36px 40px;text-align:center}}
.hd h1{{font-size:26px;letter-spacing:2px;margin-bottom:6px}}
.hd .sub{{font-size:13px;color:#a8b2d1;margin-top:6px}}
.wrap{{max-width:1100px;margin:0 auto;padding:24px 32px}}
.section-title{{font-size:16px;font-weight:700;color:#1a1a2e;margin:20px 0 12px;padding-left:10px;border-left:4px solid #4361ee}}
.rank-table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.06);margin-bottom:24px;font-size:13px}}
.rank-table th{{background:#1a1a2e;color:#fff;padding:10px 16px;text-align:center}}
.rank-table td{{padding:10px 16px;border-bottom:1px solid #f1f5f9;text-align:center}}
.model-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:24px}}
.model-card{{background:#fff;border-radius:12px;padding:20px;box-shadow:0 4px 16px rgba(0,0,0,0.06)}}
.model-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #f1f5f9}}
.model-id{{font-size:20px;font-weight:900;color:#1a1a2e;font-family:Consolas,monospace}}
.model-name{{font-size:13px;color:#888;margin-left:6px}}
.avg-badge{{font-size:15px;font-weight:900;padding:4px 14px;border-radius:20px}}
.task-row{{background:#f8fafc;border-radius:8px;padding:12px 14px;margin-bottom:8px;border-left:3px solid #e2e8f0}}
.task-title{{font-size:12px;color:#444;margin-bottom:6px;font-weight:600}}
.task-score{{display:flex;align-items:center;gap:8px;margin-bottom:4px}}
.badge{{font-weight:700;font-size:13px;padding:2px 10px;border-radius:10px}}
.badge-sm{{font-size:11px;color:#888;background:#f1f5f9;padding:1px 7px;border-radius:8px}}
.task-note{{font-size:11px;color:#64748b;line-height:1.5}}
.human-summary{{margin-top:12px;padding:10px;background:#fffbea;border-radius:6px;font-size:12px;color:#92400e;line-height:1.6;border-left:3px solid #f59e0b}}
.ft{{text-align:center;padding:20px;color:#999;font-size:12px;border-top:1px solid #e2e8f0;margin-top:20px}}
</style>
</head>
<body>

<div class="hd">
    <h1>评测报告（纯文字版）</h1>
    <div class="sub">
        4个模型 × 3个任务 &nbsp;|&nbsp;
        DQX6D(queen) · I2QS4(bishop) · KVAZ2(rook) · 9CNZI(knight)<br>
        评分维度：需求完成度(0-5) + 代码质量(0-3) + 轨迹质量(0-2) = 满分10<br>
        生成时间：{now}
    </div>
</div>

<div class="wrap">
    <div class="section-title">综合排名</div>
    <table class="rank-table">
        <tr>
            <th>排名</th><th>模型ID</th><th>昵称</th>
            <th>JWNK6P<br>V模型追溯</th>
            <th>TRW23D<br>Git配置</th>
            <th>GO7Q83<br>MAP解析</th>
            <th>平均分</th>
        </tr>
        {rank_rows}
    </table>

    <div class="section-title">各模型详细评分</div>
    <div class="model-grid">
        {model_cards}
    </div>
</div>

<div class="ft">评测报告（纯文字版） · 生成时间：{now} · 佐证截图见 ev_*.png 文件</div>
</body>
</html>"""
    return html


def main():
    html = build_html()
    out_file = os.path.join(OUT, "eval_report_20260516_text.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)
    sz = os.path.getsize(out_file)
    print(f"[OK] 纯文字版报告: {out_file}")
    print(f"     Size: {sz // 1024} KB")


if __name__ == "__main__":
    main()
