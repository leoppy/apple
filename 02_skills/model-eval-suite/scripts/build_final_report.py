#!/usr/bin/env python3
"""生成最终报告：每张截图紧跟在对应打分评语后面。"""

import base64, os

OUT = r'D:\01_github\banana\apple\02_skills\model-eval-suite\03_results'

# 读取截图 base64
def b64(name):
    p = os.path.join(OUT, name)
    with open(p, 'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()

IMG = {
    '2m_needs':  b64('ev_2MA1KK_needs.png'),
    '2m_code1':  b64('ev_2MA1KK_code1.png'),
    '2m_code2':  b64('ev_2MA1KK_code2.png'),
    'lq_needs':  b64('ev_LNQOQQ_needs.png'),
    'lq_code':   b64('ev_LNQOQQ_code.png'),
    'qj_needs': b64('ev_QJHYG3_needs.png'),
    'qj_code':   b64('ev_QJHYG3_code.png'),
}

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>mn2 (AXWAI) 评测报告</title>
<style>
:root {{
    --bg:#f0f2f5; --card:#fff; --pri:#1a1a2e; --accent:#4361ee;
    --ok:#06d6a0; --warn:#ffd166; --danger:#ef476f;
    --muted:#8d99ae; --border:#e2e8f0;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Microsoft YaHei','Segoe UI',sans-serif; background:var(--bg); color:#2b2d42; line-height:1.7; }}

/* Header */
.hd {{ background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460); color:#fff; padding:36px 40px; text-align:center; }}
.hd h1 {{ font-size:28px; letter-spacing:2px; margin-bottom:6px; }}
.hd .sub {{ font-size:14px; color:#a8b2d1; }}
.hd .meta {{ margin-top:12px; font-size:13px; color:#8892b0; }}

/* Summary */
.sum {{ max-width:1400px; margin:0 auto; padding:24px 40px; }}
.cards {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:20px; }}
.card {{ background:var(--card); border-radius:14px; padding:20px 24px; box-shadow:0 4px 20px rgba(0,0,0,0.06); border-top:3px solid var(--accent); }}
.card h3 {{ font-size:16px; color:var(--pri); margin-bottom:8px; }}
.card .desc {{ font-size:12px; color:var(--muted); margin-bottom:12px; }}
.pills {{ display:flex; gap:8px; flex-wrap:wrap; }}
.pill {{ padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }}
.pill.ok   {{ background:#d1fae5; color:#065f46; }}
.pill.warn {{ background:#fef3c7; color:#92400e; }}
.pill.dim  {{ background:#e0e7ff; color:#3730a3; }}
.pill.total {{ background:linear-gradient(135deg,#4361ee,#7c3aed); color:#fff; font-size:14px; padding:4px 14px; }}
.total-bar {{ background:var(--card); border-radius:14px; padding:20px 28px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 4px 20px rgba(0,0,0,0.06); }}
.total-bar .big {{ font-size:32px; font-weight:900; color:var(--accent); }}
.total-bar .note {{ font-size:13px; color:var(--muted); }}

/* Task Detail */
.tasks {{ max-width:1400px; margin:0 auto; padding:0 40px 40px; }}
.task {{ background:var(--card); border-radius:14px; padding:28px 32px; margin-bottom:24px; box-shadow:0 4px 20px rgba(0,0,0,0.06); }}
.task h2 {{ font-size:20px; color:var(--pri); margin-bottom:4px; display:flex; align-items:center; gap:10px; }}
.task h2 .badge {{ padding:3px 12px; border-radius:12px; font-size:13px; color:#fff; }}
.task .req {{ background:#f8fafc; border-left:3px solid var(--accent); padding:10px 14px; margin:12px 0 20px; font-size:13px; color:var(--muted); }}

/* Scoring dimension block */
.dim-block {{ margin-bottom:24px; }}
.dim-block h3 {{ font-size:16px; color:var(--pri); margin-bottom:10px; display:flex; align-items:center; gap:8px; }}
.dim-block h3 .dscore {{ background:var(--accent); color:#fff; padding:2px 10px; border-radius:10px; font-size:12px; }}
.dim-block .comment {{ font-size:14px; line-height:1.8; color:#374151; margin-bottom:12px; }}
.dim-block .comment .ok   {{ color:#059669; font-weight:600; }}
.dim-block .comment .bad  {{ color:#dc2626; font-weight:600; }}
.dim-block .comment .note {{ color:var(--muted); font-size:13px; }}

/* Evidence screenshot — key:紧贴评语 */
.ev-img {{ border:1px solid var(--border); border-radius:10px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.06); margin-top:8px; }}
.ev-img img {{ width:100%; height:auto; display:block; }}

/* Footer */
.ft {{ text-align:center; padding:24px; color:var(--muted); font-size:12px; border-top:1px solid var(--border); margin-top:20px; }}
</style>
</head>
<body>

<div class="hd">
    <h1>📋 模型评测报告</h1>
    <div class="sub">mn2 (AXWAI) — 模型无关评测任务集</div>
    <div class="meta">评测时间：2026-05-09 ｜ 佐证方式：代码关键行截图</div>
</div>

<div class="sum">
    <div class="cards">
        <div class="card">
            <h3>📝 2MA1KK</h3>
            <div class="desc">Word 文档批量修改（V3.0 版本升级）</div>
            <div class="pills">
                <span class="pill ok">需求 5/5</span>
                <span class="pill warn">代码 2/3</span>
                <span class="pill dim">轨迹 1/2</span>
                <span class="pill total">8/10</span>
            </div>
        </div>
        <div class="card">
            <h3>📊 LNQOQQ</h3>
            <div class="desc">MAP 文件解析（RAM/ROM 内存用量统计）</div>
            <div class="pills">
                <span class="pill ok">需求 3/5</span>
                <span class="pill warn">代码 2/3</span>
                <span class="pill dim">轨迹 1/2</span>
                <span class="pill total">6/10</span>
            </div>
        </div>
        <div class="card">
            <h3>🔧 QJHYG3</h3>
            <div class="desc">CANoe 硬件通道映射（注册表操作）</div>
            <div class="pills">
                <span class="pill ok">需求 5/5</span>
                <span class="pill ok">代码 3/3</span>
                <span class="pill dim">轨迹 1/2</span>
                <span class="pill total">9/10</span>
            </div>
        </div>
    </div>
    <div class="total-bar">
        <div>
            <div style="font-size:16px;font-weight:bold;">📊 综合总分</div>
            <div class="note">3 个任务，满分 30 分</div>
        </div>
        <div class="big">23 / 30 <span style="font-size:16px;color:var(--muted);">（平均 7.7）</span></div>
    </div>
</div>

<!-- ==================== TASK 1: 2MA1KK ==================== -->
<div class="tasks">
<div class="task">
    <h2>📝 2MA1KK — Word 批量修改 <span class="badge" style="background:var(--ok);">8/10</span></h2>
    <div class="req">
        <strong>需求：</strong>批量修改 9 个 Word 文档，将版本号升级到 V3.0，添加版本履历表，并做内容优化（格式/措辞/补充说明）。不篡改实质性技术参数。
    </div>

    <!-- 需求完成度 -->
    <div class="dim-block">
        <h3>需求完成度 <span class="dscore">5/5</span></h3>
        <div class="comment">
            <span class="ok">✅ 评分依据（5分满分）：</span><br>
            1. 全部 9 个文档均成功升级到 V3.0，自动验证确认每个文档的表格中均包含 V3.0 记录。<br>
            2. 每个文档都执行了三步操作：版本号更新 → 版本履历追加 → 内容优化（措辞/补充说明）。<br>
            3. 修改日志（CHANGES_LOG）完整记录了每个文档的具体变更内容，可追溯。<br>
            <span class="note">→ 下方截图直接对应 main() 中 9 个函数的逐一调用，是 "需求完成度 5/5" 的直接证据。</span>
        </div>
        <div class="ev-img"><img src="{IMG['2m_needs']}" alt="2MA1KK需求完成度佐证"></div>
    </div>

    <!-- 代码质量 -->
    <div class="dim-block">
        <h3>代码质量 <span class="dscore">2/3</span></h3>
        <div class="comment">
            <span class="ok">✅ 亮点（支撑 +1~2 分）：</span><br>
            • 通用函数封装得当：update_doc_info_table()、add_version_history()、replace_text_all()、add_tip_after() 四个通用操作函数复用性好。<br>
            • 修改日志完善：CHANGES_LOG 字典记录了每个文档的具体变更，便于审查追溯。<br><br>
            <span class="bad">⚠️ 扣分项（合计扣 1 分）：</span><br>
            1. <span class="bad">硬编码日期和作者</span>：V3_DATE 和 V3_AUTHOR 写在模块顶层，应改为参数传入或从配置文件读取。<br>
            2. <span class="bad">9 个 modify_xxx() 函数结构高度重复</span>：load→modify→save 骨架完全相同，未抽象公共逻辑，可用配置驱动消除冗余。<br>
            <span class="note">→ 下方两张截图分别对应两个扣分点，截图里黄色高亮行即是扣分依据。</span>
        </div>
        <div class="ev-img"><img src="{IMG['2m_code1']}" alt="扣分点1：硬编码"></div>
        <div style="height:10px;"></div>
        <div class="ev-img"><img src="{IMG['2m_code2']}" alt="扣分点2：重复结构"></div>
    </div>
    <div style="background:#f0fdf4;border-left:3px solid #22c55e;padding:10px 14px;margin-top:14px;border-radius:8px;font-size:13px;line-height:1.8;color:#166534;">
        💬 <strong>总结：</strong>完成度没问题，9个文档都到位了。但代码写得急，日期写死、函数重复，抽个配置驱动的公共函数出来会清爽很多。
    </div>
</div>

<!-- ==================== TASK 2: LNQOQQ ==================== -->
<div class="task">
    <h2>📊 LNQOQQ — MAP 文件解析 <span class="badge" style="background:var(--warn);color:#333;">6/10</span></h2>
    <div class="req">
        <strong>需求：</strong>解析 Green Hills ELXR linker map 文件，提取各 section 的内存占用，按 ROM/RAM 分类汇总，输出格式化的统计表。
    </div>

    <!-- 需求完成度 -->
    <div class="dim-block">
        <h3>需求完成度 <span class="dscore">3/5</span></h3>
        <div class="comment">
            <span class="ok">✅ 亮点：</span><br>
            • classify() 函数基于地址范围 + 关键字双重分类，覆盖 META/RAM/ROM/UNKNOWN 四类，逻辑严谨。<br>
            • 输出格式精美，同时输出终端表格和 Markdown 格式，方便直接粘贴到文档。<br><br>
            <span class="bad">⚠️ 扣分项（合计扣 2 分）：</span><br>
            1. <span class="bad">产物中没有 .map 文件</span>：MAP_FILE 常量硬编码为 "YL2_S32G3.map"，但该文件不存在于产物目录中，无法端到端验证解析结果是否正确。<br>
            2. <span class="bad">缺少样例输出佐证</span>：没有输出样例（如 STDOUT 重定向到 .txt），无法判断分类逻辑在实际 MAP 文件上的效果。<br>
            <span class="note">→ 下方截图展示 MAP_FILE 硬编码行和 main() 入口，高亮处即扣分依据。</span>
        </div>
        <div class="ev-img"><img src="{IMG['lq_needs']}" alt="LNQOQQ需求完成度佐证"></div>
    </div>

    <!-- 代码质量 -->
    <div class="dim-block">
        <h3>代码质量 <span class="dscore">2/3</span></h3>
        <div class="comment">
            <span class="ok">✅ 亮点（支撑 +2 分）：</span><br>
            • human() 单位转换简洁（B/KB/MB 三级覆盖）。<br>
            • group() 按前缀聚合 section，避免输出几百行冗余，只展示汇总结果，实用性强。<br>
            • classify() 地址范围分类逻辑完整，注释清晰，覆盖了 ROM、RAM、META、UNKNOWN 四类。<br><br>
            <span class="bad">⚠️ 扣分项（扣 1 分）：</span><br>
            1. <span class="bad">所有函数均无类型注解</span>，不利于静态分析和 IDE 提示。<br>
            2. <span class="bad">主流程缺少异常处理</span>，无文件存在性检查，无编码异常处理（虽然用了 errors='ignore'，但主流程无 try-except）。<br>
            <span class="note">→ 下方截图展示 classify() 函数，黄色高亮为地址分类的关键逻辑（即亮点依据）。</span>
        </div>
        <div class="ev-img"><img src="{IMG['lq_code']}" alt="LNQOQQ代码质量佐证"></div>
    </div>
    <div style="background:#f0fdf4;border-left:3px solid #22c55e;padding:10px 14px;margin-top:14px;border-radius:8px;font-size:13px;line-height:1.8;color:#166534;">
        💬 <strong>总结：</strong>classify() 地址分类写得严谨，但产物缺 .map 文件跑不起来验证。代码本身也糙，缺注解没防护，能跑但不稳。
    </div>
</div>

<!-- ==================== TASK 3: QJHYG3 ==================== -->
<div class="task">
    <h2>🔧 QJHYG3 — CANoe 通道映射 <span class="badge" style="background:var(--ok);">9/10</span></h2>
    <div class="req">
        <strong>需求：</strong>编写 Python 脚本修改 Windows 注册表，为 CANoe 配置 CAN/LIN 硬件通道映射（hwType/hwIndex/hwChannel）。<strong>明确要求不触碰 Ethernet 通道</strong>。
    </div>

    <!-- 需求完成度 -->
    <div class="dim-block">
        <h3>需求完成度 <span class="dscore">5/5</span></h3>
        <div class="comment">
            <span class="ok">✅ 评分依据（5分满分）：</span><br>
            1. 完整实现了 CAN/LIN 通道映射的注册表读写，apply_mappings() 写注册表，verify_mappings() 读回验证，形成 apply→verify 闭环。<br>
            2. 模块化设计：main.py（配置解析入口）、registry_mapping.py（注册表操作核心）、README.md（使用文档），职责清晰。<br>
            3. JSON 配置驱动，格式清晰，支持多通道批量配置。<br>
            <span class="note">→ 下方截图展示 main.py 入口代码，高亮处为 apply→verify 闭环，是 "需求完成度 5/5" 的直接证据。</span>
        </div>
        <div class="ev-img"><img src="{IMG['qj_needs']}" alt="QJHYG3需求完成度佐证"></div>
    </div>

    <!-- 代码质量 -->
    <div class="dim-block">
        <h3>代码质量 <span class="dscore">3/3</span></h3>
        <div class="comment">
            <span class="ok">✅ 满分依据（3/3）：</span><br>
            1. <span class="ok">Ethernet 三重防护</span>：bus_type 白名单检查（第52行）+ _is_ethernet_key() 名称检查（第59行）+ _key_name() 构造逻辑保证永远不生成 CANoe.ETH* 格式，三重保障不触碰 Ethernet。<br>
            2. <span class="ok">完整的类型注解</span>：所有函数和 dataclass 字段都有类型注解。<br>
            3. <span class="ok">读回验证闭环</span>：verify_mappings() 写后读回，返回结构化结果（ok 状态 + ui_channel 转换）。<br>
            4.             <span class="ok">正确使用 winreg</span>：KEY_WOW64_64KEY 确保 64 位注册表操作，context manager 保证句柄释放。<br>
            <span class="note">可再细化：apply_mappings() 的注册表写入操作未加 try-except，当前依赖调用方处理异常，建议在函数内部捕获 winreg 相关异常并给出明确错误信息。</span><br>
            <span class="note">→ 下方截图展示 apply_mappings() 函数，黄色高亮为三重 Ethernet 防护的具体代码行，是 "代码质量 3/3" 的核心证据。</span>
        </div>
        <div class="ev-img"><img src="{IMG['qj_code']}" alt="QJHYG3代码质量佐证"></div>
    </div>
    <div style="background:#f0fdf4;border-left:3px solid #22c55e;padding:10px 14px;margin-top:14px;border-radius:8px;font-size:13px;line-height:1.8;color:#166534;">
        💬 <strong>总结：</strong>完成得相当漂亮，Ethernet 三重防护到位，apply→verify 闭环也做全了。唯一可挑的就是写入注册表没加 try-except，差一口气满配。
    </div>
</div>
</div>

<div class="ft">
    mn2 (AXWAI) 评测报告 ｜ 生成时间：2026-05-09 ｜ 佐证截图 7 张（代码关键行）
</div>

</body>
</html>'''

out_path = os.path.join(OUT, 'eval_report_mn2.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(HTML)

sz = os.path.getsize(out_path)
print(f'[OK] Report written: {out_path}')
print(f'     Size: {sz//1024} KB ({sz//1024//1024} MB)')
print(f'     Screenshots embedded: 7')
