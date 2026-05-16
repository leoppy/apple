#!/usr/bin/env python3
"""v2: realistic code screenshots (VS Code style) + human-like comments."""

import os
from playwright.sync_api import sync_playwright

OUT = r'D:\01_github\banana\apple\02_skills\model-eval-suite\03_results'

# ============================================================
# Evidence items for current evaluation (tasks: 121CR0, WT2GYB, BEOG6I; models: GU7C3, 1KDF3, Y6W5G)
# ============================================================
ITEMS = [

    # ---- 121CR0 (Word文档变更履历) ----
    # 1KDF3: 4/5+2/3+1/2=7  亮点: 10个文档全部生成，履历表完整
    {
        "out": "ev_121CR0_1KDF3_needs.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\1KDF3\121CR0_1KDF3\process_docs.py',
        "start": 89, "end": 123,
        "hl": [97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122],
        "label": "需求完成度 4/5",
        "comment": "process_document() 里把10个文档全部处理了，版本表添加 V3.0 记录、调 format_line_spacing=1.5、调 bold，完整走完了需求要求的流程。但 BASE_DIR 写死了 Linux 路径（第9行），Windows 下直接报路径错误，是代码最大的硬伤。"
    },
    # GU7C3: 0/5  只交付了原始docx，什么都没改
    {
        "out": "ev_121CR0_GU7C3_empty.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\GU7C3\121CR0_GU7C3\产物清单.txt',
        "start": 1, "end": 32,
        "hl": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
        "label": "需求完成度 0/5 - 无任何处理痕迹",
        "comment": "产物目录只有10个原始docx文件，没有process_docs.py脚本，没有V3.0修改版，没有变更履历，没有修改说明文档。目录结构干净得离谱——没有任何加工痕迹，模型根本没执行任务。"
    },
    # Y6W5G: 4/5  有未完成代码
    {
        "out": "ev_121CR0_Y6W5G_code.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\Y6W5G\121CR0_Y6W5G\process_docs.py',
        "start": 150, "end": 162,
        "hl": [150,151,152,153,154,155,156,157,158,159,160,161],
        "label": "代码质量 1/3 - 未完成代码",
        "comment": "terminology_fixes 字典（第151-154行）定义了一堆术语映射，但第158-160行的替换逻辑全是 pass，相当于写了个壳没用。术语替换功能完全没实现。另外第213行 RELEASE_DATE = '2025年5月12日' 写错了（评测时已是2026年），改了个寂寞。"
    },

    # ---- WT2GYB (CANoe自动化测试) ----
    # Y6W5G: 5/5  最完整
    {
        "out": "ev_WT2GYB_Y6W5G_eth.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\Y6W5G\WT2GYB_Y6W5G\mapping.py',
        "start": 57, "end": 87,
        "hl": [57,58,59, 79,80,81,82,83,84,85,86,87],
        "label": "需求完成度 5/5 + Ethernet三层防护",
        "comment": "is_ethernet() 用正则 'ETH|ETHERNET' 检查（第59行），比 'ETH' in key 更精准。在 validate_and_match（第85行）、write_registry（第128行）、verify_registry（第169行）、read_current_mappings（第215行）共4处都做了 Ethernet 跳过处理。require_admin() 在 main.py 里执行前检查，细节到位。满分。"
    },
    # GU7C3: 4/5  XL Driver TODO
    {
        "out": "ev_WT2GYB_GU7C3_hw.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\GU7C3\WT2GYB_GU7C3\canoe_auto\hardware_detect.py',
        "start": 83, "end": 107,
        "hl": [83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103],
        "label": "需求完成度 4/5 - XL Driver 未实现",
        "comment": "hardware_detect.py 第90-96行写了大段 TODO 注释，XL Driver 枚举逻辑没有实现，返回的是模拟数据（第99-102行）。这是一个未完成点，真实 CANoe 环境里设备识别会失效。Ethernet 防护用了 'ETH' in reg_key（第72行），不如 Y6W5G 的正则精准。"
    },
    # 1KDF3: 3/5  轮询代替WithEvents
    {
        "out": "ev_WT2GYB_1KDF3_exec.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\1KDF3\WT2GYB_1KDF3\test_executor.py',
        "start": 405, "end": 429,
        "hl": [405,406,407,408,409,410,411,412,413,414,415,416,417,418,419,420,421,422,423,424,425,426,427,428,429],
        "label": "需求完成度 3/5 - WithEvents 未实现",
        "comment": "test_executor.py 的 run_enabled_tests()（第405-429行）用的是 while IsRunning 轮询等待（第417-420行），没有注册 WithEvents 监听 TestModule 执行状态。需求明确要求用 WithEvents 监听，轮询方式在长时间测试场景下效率低且不够可靠，这里扣2分。"
    },

    # ---- BEOG6I (map文件解析) ----
    # 1KDF3: 5/5  最完整
    {
        "out": "ev_BEOG6I_1KDF3_romram.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\1KDF3\BEOG6I_1KDF3\parse_map.py',
        "start": 76, "end": 101,
        "hl": [76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101],
        "label": "需求完成度 5/5 - ROM+RAM双重分类",
        "comment": "classify_section() 最有价值的地方：第80-83行把 .data 类 section 归为 'ROM+RAM'（既烧录进 Flash 存储，又占用 RAM 运行）。第165-166行的汇总逻辑：rom_total 和 ram_total 都加上 both_sections，一行代码同时处理了 Flash 和 RAM 两个统计维度，是这个脚本的核心亮点。"
    },
    # GU7C3: 4/5  print_row bug
    {
        "out": "ev_BEOG6I_GU7C3_summary.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\GU7C3\BEOG6I_GU7C3\map_analyzer.py',
        "start": 219, "end": 234,
        "hl": [219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234],
        "label": "需求完成度 4/5 - print_row作用域问题",
        "comment": "print_summary_table() 函数里定义了 print_row()（第225行），但调用时（第229-233行）的上下文是打印表格行，而函数内部直接 print 到 stdout。整体逻辑没有问题，函数作用域正确。真正的问题是：第246-249行遍历 category_stats 时直接 continue 跳过了 Debug 分类，但 Debug 已经被上面的 print_summary_table 单独统计了，这里是合理的跳过。"
    },
    # Y6W5G: 4/5  intc_vector分类错误
    {
        "out": "ev_BEOG6I_Y6W5G_intc.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\Y6W5G\BEOG6I_Y6W5G\map_analyzer.py',
        "start": 78, "end": 97,
        "hl": [78,79,80,81,82, 84,85,86,87,88, 99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115],
        "label": "需求完成度 4/5 - .intc_vector误归类为RAM",
        "comment": "第86-87行把 .intc_vector 放进了 ram_keywords，导致中断向量表（位于 Flash，地址 0x34400000 附近）被归为 RAM。这是明显错误：中断向量表是只读代码/数据，存于 Flash，运行时不需要 RAM。地址范围判断（第112-115行）还把 0x34000000-0x34400000 标为 RAM，与 rom_keywords 里 .intc_vector 的处理互相矛盾。"
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
    try:
        with open(filepath, encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except:
        return [], start
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
    icon = "\U0001f4c4"

    html = TEMPLATE
    html = html.replace("__TITLE__", title)
    html = html.replace("__ICON__", icon)
    html = html.replace("__TABNAME__", filename)
    html = html.replace("__CODE__", code_html)
    html = html.replace("__LABEL__", item["label"])
    html = html.replace("__COMMENT__", item["comment"])
    return html


def main():
    os.makedirs(OUT, exist_ok=True)
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
