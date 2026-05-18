#!/usr/bin/env python3
"""v2: realistic code screenshots (VS Code style) + human-like comments."""

import os
from playwright.sync_api import sync_playwright

OUT = r'D:\01_github\banana\apple\02_skills\model-eval-suite\03_results'

# ============================================================
# Evidence items for current evaluation
# Tasks: JWNK6P, TRW23D, GO7Q83
# Models: DQX6D(queen), I2QS4(bishop), KVAZ2(rook), 9CNZI(knight)
# ============================================================
# 填写指南：
#   "out"     → 输出文件名，格式: ev_<任务ID>_<模型ID>_<标签>.png
#   "file"    → 产物中要截取的 .py 文件绝对路径
#   "start"   → 截取起始行（含）
#   "end"     → 截取结束行（含）
#   "hl"      → 黄色高亮行号列表
#   "label"   → 截图底部标签（如 "需求完成度 4/5"）
#   "comment" → 底部评语，口语化，指向具体行号，不用AI套话
# ============================================================
ITEMS = [

    # ---- JWNK6P ----
    # queen / DQX6D
    {
        "out": "ev_JWNK6P_DQX6D_req.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\DQX6D\JWNK6P_DQX6D\v_model_tracer.py',
        "start": 39, "end": 95,
        "hl": [44, 46, 47, 83, 84, 85, 86, 87, 88],
        "label": "需求完成度 4/5",
        "comment": "CLI 参数与需求文档基本对齐（第44行 --report-type required，第46-47行 --verbose/-v），主流程拆分到独立模块，覆盖率/通过率报告分支清晰（第83-88行）。缺少 .env 加载路径 02_skills/token-manager，且日志文件未按需求写到 tempFile/logs 的相对路径，扣1分。"
    },
    # bishop / I2QS4
    {
        "out": "ev_JWNK6P_I2QS4_req.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\I2QS4\JWNK6P_I2QS4\v_model_tracer.py',
        "start": 42, "end": 117,
        "hl": [44, 46, 47, 49, 50, 71, 72, 73, 74, 75, 76, 96, 97, 98],
        "label": "需求完成度 4/5",
        "comment": "CLI 对齐完整，--no-cache、--project、--output、--log 均实现（第44-50行）。报告输出路径按 tempFile/reports/YYYYMMDD 拼接（第96-98行），缓存manager独立实例化（第71-76行）。.env 加载未指定 token-manager 路径，稍有偏差，扣1分。"
    },
    # rook / KVAZ2
    {
        "out": "ev_JWNK6P_KVAZ2_req.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\KVAZ2\JWNK6P_KVAZ2\v_model_tracer.py',
        "start": 38, "end": 99,
        "hl": [41, 42, 56, 57, 58, 59, 60, 104, 105, 106, 107, 108, 109],
        "label": "需求完成度 5/5",
        "comment": "CLI 参数完全对齐，parse_args 独立函数（第38-77行），--no-cache、--project、--report-type、--output、--log 全部覆盖（第41-76行）。apply_cli_overrides 机制干净，get_env_vars 统一读取环境变量，r4j_projects/confluence_testcases 流程分明，输出路径 tempFile/reports/YYYYMMDD 符合规范，满分。"
    },
    # knight / 9CNZI
    {
        "out": "ev_JWNK6P_9CNZI_req.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\9CNZI\JWNK6P_9CNZI\v_model_tracer.py',
        "start": 70, "end": 82,
        "start2": 1038, "end2": 1065,
        "hl": [71, 72, 73, 74, 1043, 1044, 1045, 1046, 1047, 1048, 1049, 1050, 1051, 1052, 1053, 1054, 1055, 1056, 1057, 1058, 1059, 1060],
        "label": "需求完成度 5/5",
        "comment": "单文件完整实现，.env 加载路径精确指向 02_skills/token-manager（第73行），CLI 参数全覆盖（第1043-1060行），load_env() 函数优先读相对路径再 fallback 本地，与需求说明的 token-manager 集成一致，满分。"
    },

    # ---- TRW23D ----
    # queen / DQX6D
    {
        "out": "ev_TRW23D_DQX6D_req.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\DQX6D\TRW23D_DQX6D\git_config.py',
        "start": 29, "end": 55,
        "hl": [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 52, 53, 54],
        "label": "需求完成度 4/5",
        "comment": "主菜单选项1-8完整，别名列表与需求完全一致（第40-49行），全局选项submodule.recurse=true（第52-54行），dry-run/SSH生成/GitHub上传逻辑均实现。用户名空值保护和API网络异常处理均有。SSH查重逻辑用key字符串比较（非指纹），有误判风险，扣1分。"
    },
    # bishop / I2QS4
    {
        "out": "ev_TRW23D_I2QS4_req.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\I2QS4\TRW23D_I2QS4\git_config.py',
        "start": 12, "end": 24,
        "start2": 456, "end2": 527,
        "hl": [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468],
        "label": "需求完成度 4/5",
        "comment": "GIT_ALIASES 字典定义6条别名全部正确（第12-18行），GIT_CONFIG_OPTIONS 可扩展结构符合需求（第20-22行）。主菜单8项完整，check_git_installed 在 dry_run 时调用 run_command 会直接执行 git --version（非干跑），逻辑有小问题。键盘中断捕获和用户名空值保护完整（第521行），扣1分。"
    },
    # rook / KVAZ2
    {
        "out": "ev_TRW23D_KVAZ2_req.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\KVAZ2\TRW23D_KVAZ2\git_config.py',
        "start": 99, "end": 130,
        "hl": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 113, 114, 115],
        "label": "需求完成度 5/5",
        "comment": "ALIASES/GLOBAL_OPTIONS 定义为类属性（第103-115行），符合需求的「可扩展」要求。_exec_git_config 封装漂亮，dry-run 下打印命令不执行（第133-135行），_api_request 通用层简化上传代码，指纹级查重防误判，main 入口 KeyboardInterrupt 捕获，满分。"
    },
    # knight / 9CNZI
    {
        "out": "ev_TRW23D_9CNZI_req.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\9CNZI\TRW23D_9CNZI\git_config.py',
        "start": 30, "end": 56,
        "hl": [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 51, 52, 53, 54],
        "label": "需求完成度 4/5",
        "comment": "别名列表6条全部正确（第40-49行），全局选项使用列表格式（第51-54行）符合扩展要求。干跑模式、SSH生成、用户名邮箱空值保护均完整。交互流程在选项执行后询问「是否继续」符合规范（第510-511行）。GitLab上传缺少422已存在的错误处理分支，扣1分。"
    },

    # ---- GO7Q83 ----
    # queen / DQX6D
    {
        "out": "ev_GO7Q83_DQX6D_req.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\DQX6D\GO7Q83_DQX6D\parse_map.py',
        "start": 1, "end": 52,
        "hl": [31, 32, 33, 34, 36, 37, 38, 39, 42, 43, 44, 45, 46, 49, 50, 51, 52],
        "label": "需求完成度 3/5",
        "comment": "实现了RAM/ROM分类和汇总表格输出，基本满足「汇总RAM和ROM总量」需求。但分类规则粗糙，else分支将PFE、LLCE等全归ROM（第43-46行），未区分调试段和实际ROM，.data段未按双重记录处理，分类准确性明显不足。"
    },
    # bishop / I2QS4
    {
        "out": "ev_GO7Q83_I2QS4_req.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\I2QS4\GO7Q83_I2QS4\map_analyzer.py',
        "start": 13, "end": 68,
        "hl": [22, 23, 24, 25, 28, 29, 48, 49, 50, 51, 52, 53, 54, 63, 64, 65, 66, 67, 68],
        "label": "需求完成度 4/5",
        "comment": "SectionInfo 面向对象设计，_classify 方法支持 DEBUG/ROM/RAM/BOTH 四分类（第22-67行），.data 段双重记录（第48-51行）是正确的嵌入式理解。get_rom_size/get_ram_size 方法封装好（第69-83行），汇总表格清晰。输出稍显繁琐，行命令参数读取方式稍显简单，扣1分。"
    },
    # rook / KVAZ2
    {
        "out": "ev_GO7Q83_KVAZ2_req.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\KVAZ2\GO7Q83_KVAZ2\parse_map.py',
        "start": 44, "end": 111,
        "hl": [44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105],
        "label": "需求完成度 5/5",
        "comment": "ROM/RAM Pattern 用正则数组定义（第44-105行），S32G3 内存区域注释完整，5张输出表（段详情/ROM分析/RAM分析/内存区域汇总/Top30模块），RAM子分类分析功能超出需求范围，属于加分项。分类准确，满分。"
    },
    # knight / 9CNZI
    {
        "out": "ev_GO7Q83_9CNZI_req.png",
        "file": r'D:\01_github\banana\apple\02_skills\model-eval-suite\02_artifacts\9CNZI\GO7Q83_9CNZI\parse_map.py',
        "start": 80, "end": 125,
        "hl": [81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123],
        "label": "需求完成度 5/5",
        "comment": "classify_memory 函数逻辑清晰，BOTH/ROM/RAM/DEBUG/SKIP 五分类精确，.data 双重计入（第108-109行），SecOffs 作为最终 fallback（第212-217行）是正确的 GHS linker 理解。parse_image_summary 专门解析 Image Summary 节（第151行），最终汇总表格用方框字符输出，清晰专业，满分。"
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
