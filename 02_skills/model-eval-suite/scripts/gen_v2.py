#!/usr/bin/env python3
"""v2: realistic code screenshots (VS Code style) + human-like comments."""

import os
from playwright.sync_api import sync_playwright

OUT = r'D:\01_github\banana\apple\02_skills\model-eval-suite\03_results'

# ============================================================
# Evidence items. Each comment is a SINGLE-LINE string to avoid syntax errors.
# ============================================================
ITEMS = [

    # ---- 2MA1KK ----
    {
        "out": "ev_2MA1KK_needs.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\mn2\2MA1KK_AXWAI\modify_docs.py',
        "start": 413, "end": 433,
        "hl": [413,414,415,416,417,418,419,420,421,422],
        "label": "需求完成度 5/5",
        "comment": "main() 里 9 个函数一个不落，对应需求里要求的 9 个文档。每个文档都做了版本号更新、版本履历追加、内容优化三步，用 CHANGES_LOG 记录了每步变更，可追溯。给满分，没争议。"
    },
    {
        "out": "ev_2MA1KK_code1.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\mn2\2MA1KK_AXWAI\modify_docs.py',
        "start": 11, "end": 16,
        "hl": [14,15],
        "label": "代码质量 2/3 - 扣分项",
        "comment": "V3_DATE 和 V3_AUTHOR 直接写死在文件头部，哪天要改日期或作者得改代码。正确做法应该是从命令行参数或配置文件读入，不该硬编码。这是第一个扣分点。"
    },
    {
        "out": "ev_2MA1KK_code2.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\mn2\2MA1KK_AXWAI\modify_docs.py',
        "start": 186, "end": 215,
        "start2": 217, "end2": 240,
        "hl": [186,187,188, 217,218,219],
        "label": "代码质量 2/3 - 扣分项",
        "comment": "modify_116 到 modify_93 一共 9 个函数，骨架完全一样：打开文档、调 update_doc_info_table、调 add_version_history、save。这种重复说明设计上没有抽象好，应该用一个配置列表加一个通用 modify() 函数来解决。这是第二个扣分点，两项各扣 0.5 分。"
    },

    # ---- LNQOQQ ----
    {
        "out": "ev_LNQOQQ_needs.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\mn2\LNQOQQ_AXWAI\parse_map.py',
        "start": 10, "end": 10,
        "start2": 129, "end2": 138,
        "hl": [10, 134,135,136,137],
        "label": "需求完成度 3/5 - 扣分项",
        "comment": "代码里默认读 YL2_S32G3.map，但这个文件不在产物里。虽然支持命令行传参，但评测时没法端到端跑一遍验证结果对不对。也没有任何示例输出（比如把 stdout 重定向到 .txt），所以需求完成度只能给 3 分：功能写了，但没法验证对错。"
    },
    {
        "out": "ev_LNQOQQ_code.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\mn2\LNQOQQ_AXWAI\parse_map.py',
        "start": 71, "end": 127,
        "hl": [87,88,89,90,91,92, 95,96, 103,104,105,106,107,108,109,110, 114,115,116,117,118,119,120, 123,124],
        "label": "代码质量 2/3 - 有亮点也有缺陷",
        "comment": "classify() 这个函数写得还不错，地址范围加关键字双重判断，META、RAM、ROM、UNKNOWN 四类都覆盖了，注释里还写了每个地址范围的用途。但整个文件缺类型注解，main() 里也没有文件存在性检查，属于能跑但对异常没防护的水平。给 2 分。",
    },

    # ---- QJHYG3 ----
    {
        "out": "ev_QJHYG3_needs.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\mn2\QJHYG3_AXWAI\main.py',
        "start": 1, "end": 30,
        "hl": [1,2,3,4,5, 19,20,21,22,23,24,25, 27,28,29],
        "label": "需求完成度 5/5",
        "comment": "main.py 读 JSON 配置，调 apply_mappings 写注册表，再调 verify_mappings 读回验证。apply 到 verify 的闭环做得很完整，不是只写不验。另外还有 README.md，JSON 配置格式写得很清楚。需求要求的功能全部实现了，给满分。",
    },
    {
        "out": "ev_QJHYG3_code.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\mn2\QJHYG3_AXWAI\registry_mapping.py',
        "start": 33, "end": 72,
        "hl": [40,41,42, 45,46,47,48,49,50,51,52,53,54,55,56, 58,59,60,61,62],
        "label": "代码质量 3/3 - Ethernet 三重防护",
        "comment": "这段是得分最高的地方。Ethernet 防护做了三层：第 52 行 bus_type 白名单，只让 CAN 和 LIN 过；第 59 行 _is_ethernet_key() 二次检查，即使 bus_type 传错了也能拦住；加上 _key_name() 的构造逻辑本身就不会生成 CANoe.ETH 格式的 key，这是第三层。类型注解齐全，winreg 用了 context manager 和 KEY_WOW64_64KEY，细节到位。代码质量给 3 分没问题。",
    },
]


# ============================================================
# HTML template: simulate VS Code dark theme window
# ============================================================
TEMPLATE = (
    '<!DOCTYPE html><html><head><meta charset="utf-8">'
    '<style>'
    '*{margin:0;padding:0;box-sizing:border-box}'
    'body{background:#1e1e1e;display:flex;justify-content:center;padding:20px 0;font-family:"Segoe UI",sans-serif}'
    '.win{width:960px;border-radius:8px;overflow:hidden;box-shadow:0 16px 48px rgba(0,0,0,0.5)}'
    '.tbar{background:linear-gradient(180deg,#3c3c3c,#2d2d2d);height:32px;display:flex;align-items:center;padding:0 12px;border-bottom:1px solid #1a1a1a;user-select:none}'
    '.tl{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:8px}'
    '.tl0{background:#ff5f57}.tl1{background:#febc2e}.tl2{background:#28c840}'
    '.ttl{flex:1;color:#c0c0c0;font-size:12px;text-align:center;margin-right:60px}'
    '.tbar2{background:#252526;height:36px;display:flex;align-items:center;padding:0 8px;border-bottom:1px solid #1e1e1e}'
    '.tab{background:#1e1e1e;color:#c0c0c0;font-size:12px;padding:6px 14px;border-top:2px solid #007acc;border-right:1px solid #1e1e1e;display:flex;align-items:center;gap:6px}'
    '.code{background:#1e1e1e;padding:8px 0}'
    '.row{display:flex;line-height:19px;min-height:19px;padding:0}'
    '.row.hl{background:rgba(255,200,0,0.10);border-left:3px solid #ffd866;padding-left:0}'
    '.ln{display:inline-block;width:52px;text-align:right;padding-right:12px;color:#5a5a5a;font-size:12.5px;font-family:"Cascadia Code","Consolas",monospace;user-select:none;flex-shrink:0}'
    '.cd{font-family:"Cascadia Code","Consolas",monospace;font-size:12.5px;color:#d4d4d4;white-space:pre;padding-left:8px}'
    '.cbar{background:#2d2d2d;border-top:1px solid #1a1a1a;padding:10px 16px;font-size:13px;color:#c0c0c0;line-height:1.7;font-family:"Microsoft YaHei","Segoe UI",sans-serif}'
    '.ctag{display:inline-block;background:#0e639c;color:#fff;padding:1px 8px;border-radius:3px;font-size:11px;font-weight:600;margin-bottom:4px;display:inline-block}'
    '</style></head><body>'
    '<div class="win">'
    '<div class="tbar">'
    '<span class="tl tl0"></span><span class="tl tl1"></span><span class="tl tl2"></span>'
    '<span class="ttl">__TITLE__</span>'
    '</div>'
    '<div class="tbar2"><div class="tab">__ICON__  __TABNAME__</div></div>'
    '<div class="code">__CODE__</div>'
    '<div class="cbar"><span class="ctag">__LABEL__</span><br>__COMMENT__</div>'
    '</div></body></html>'
)


def read_seg(filepath, start, end):
    with open(filepath, encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    s = max(0, start - 1)
    e = min(len(lines), end)
    return lines[s:e], start


def build_code_html(item):
    filepath = item["file"]
    hl = set(item["hl"])

    seg1, off1 = read_seg(filepath, item["start"], item["end"])
    parts = []
    for i, line in enumerate(seg1):
        ln = off1 + i
        cls = " hl" if ln in hl else ""
        escaped = line.rstrip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        parts.append('<div class="row{}"><span class="ln">{}</span><span class="cd">{}</span></div>'.format(cls, ln, escaped))

    if "start2" in item:
        seg2, off2 = read_seg(filepath, item["start2"], item["end2"])
        for i, line in enumerate(seg2):
            ln = off2 + i
            cls = " hl" if ln in hl else ""
            escaped = line.rstrip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            parts.append('<div class="row{}"><span class="ln">{}</span><span class="cd">{}</span></div>'.format(cls, ln, escaped))

    return "\n".join(parts)


def render(item):
    code_html = build_code_html(item)
    filename = os.path.basename(item["file"])
    folder = os.path.basename(os.path.dirname(item["file"]))
    title = "{} \u2014 {}".format(folder, filename)
    icon = "\U0001f4c4"  # 

    html = TEMPLATE
    html = html.replace("__TITLE__", title)
    html = html.replace("__ICON__", icon)
    html = html.replace("__TABNAME__", filename)
    html = html.replace("__CODE__", code_html)
    html = html.replace("__LABEL__", item["label"])
    html = html.replace("__COMMENT__", item["comment"])
    return html


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1000, "height": 800}, device_scale_factor=2)
        page = ctx.new_page()

        for item in ITEMS:
            html = render(item)
            page.set_content(html, wait_until="networkidle")
            page.wait_for_timeout(400)
            height = page.evaluate("document.documentElement.scrollHeight")
            page.set_viewport_size({"width": 1000, "height": max(height, 800)})

            out = os.path.join(OUT, item["out"])
            page.screenshot(path=out, full_page=True)
            sz = os.path.getsize(out)
            print("  OK  {}  ({}KB)".format(item["out"], sz // 1024))

        browser.close()
    print("\nDone. {} screenshots.".format(len(ITEMS)))


if __name__ == "__main__":
    main()
