#!/usr/bin/env python3
"""生成简洁汇总报告：HTML 只展示评价矩阵，截图以独立文件形式存在。"""

import os

OUT = r'D:\01_github\banana\apple\02_skills\model-eval-suite\03_results'

HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>模型评测报告</title>
<style>
:root {--bg:#f0f2f5;--card:#fff;--pri:#1a1a2e;--accent:#4361ee;--ok:#06d6a0;--warn:#ffd166;--danger:#ef476f;--muted:#8d99ae;--border:#e2e8f0;}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Microsoft YaHei','Segoe UI',sans-serif;background:var(--bg);color:#2b2d42;line-height:1.7}
.hd{background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);color:#fff;padding:36px 40px;text-align:center}
.hd h1{font-size:28px;letter-spacing:2px;margin-bottom:6px}
.hd .sub{font-size:14px;color:#a8b2d1}
.hd .meta{margin-top:12px;font-size:13px;color:#8892b0}
.wrap{max-width:1400px;margin:0 auto;padding:24px 40px}

/* ====== 模型代号对照表 ====== */
.code-map{background:#1e1e1e;border-radius:14px;padding:24px 32px;margin-bottom:20px;border:1px solid #3a3a5c}
.code-map h2{font-size:16px;color:#e0e0ff;margin-bottom:16px;letter-spacing:1px}
.code-map .mapping{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.code-map .m-item{background:#2a2a3e;border-radius:10px;padding:14px 18px;border-left:4px solid var(--accent)}
.code-map .m-code{font-size:22px;font-weight:900;color:#ffd866;margin-bottom:4px;font-family:'Consolas',monospace}
.code-map .m-name{font-size:14px;color:#a0a0cc}
.code-map .m-note{font-size:12px;color:#7070aa;margin-top:4px}

/* ====== 评测总览（三模型卡片）====== */
.overview{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px}
.ov-card{background:#fff;border-radius:14px;padding:22px 24px;box-shadow:0 4px 20px rgba(0,0,0,0.06);border-top:3px solid var(--accent)}
.ov-card h3{font-size:17px;color:var(--pri);margin-bottom:6px;display:flex;align-items:center;justify-content:space-between}
.ov-card .avg-badge{background:linear-gradient(135deg,#4361ee,#7c3aed);color:#fff;font-size:15px;font-weight:900;padding:3px 12px;border-radius:20px}
.ov-task{background:#f8fafc;border-radius:8px;padding:10px 14px;margin-bottom:8px;border-left:3px solid var(--muted)}
.ov-task .tname{font-size:12px;color:var(--muted);margin-bottom:4px}
.ov-task .tscore{display:flex;align-items:center;gap:8px}
.score-pill{font-weight:700;font-size:14px;padding:2px 10px;border-radius:12px}
.score-pill.s-ok{background:#d1fae5;color:#065f46}
.score-pill.s-warn{background:#fef3c7;color:#92400e}
.score-pill.s-bad{background:#fee2e2;color:#991b1b}
.score-pill.s-total{background:linear-gradient(135deg,#4361ee,#7c3aed);color:#fff;font-size:12px;padding:2px 8px}
.t-desc{font-size:12px;color:#64748b;margin-top:4px;line-height:1.5}

/* ====== 综合排名表 ====== */
.score-table{width:100%;border-collapse:collapse;margin-bottom:20px;font-size:13px;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.06)}
.score-table th{background:#1a1a2e;color:#fff;padding:10px 14px;text-align:center;border-bottom:2px solid #2a2a4e}
.score-table td{padding:9px 14px;border-bottom:1px solid #f1f5f9;text-align:center}
.score-table tr:last-child td{border-bottom:none}
.score-table .t-ok{color:#059669;font-weight:700}
.score-table .t-warn{color:#d97706;font-weight:700}
.score-table .t-bad{color:#dc2626;font-weight:700}
.score-table .t-total{background:#eff6ff;font-weight:900;font-size:15px}
.score-table .rank{font-size:20px}

/* ====== 任务小卡片 ====== */
.task-pills{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.task-pill{background:#fff;border-radius:12px;padding:16px 20px;box-shadow:0 2px 12px rgba(0,0,0,0.05)}
.task-pill h4{font-size:14px;color:var(--pri);margin-bottom:4px}
.task-pill .t-tag{font-size:11px;color:var(--muted);margin-bottom:8px}
.pills{display:flex;gap:6px;flex-wrap:wrap}
.pill{padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
.pill.ok{background:#d1fae5;color:#065f46}
.pill.warn{background:#fef3c7;color:#92400e}
.pill.danger{background:#fee2e2;color:#991b1b}

.ft{text-align:center;padding:24px;color:var(--muted);font-size:12px;border-top:1px solid var(--border);margin-top:20px}
</style>
</head>
<body>

<div class="hd">
    <h1>模型评测报告</h1>
    <div class="sub">3 个任务 × 3 个模型横向对比 &nbsp;|&nbsp; Y6W5G=7.3 &nbsp;1KDF3=7.3 &nbsp;GU7C3=5.7</div>
    <div class="meta">评测时间：2026-05-12 &nbsp;|&nbsp; 佐证截图 9 张（独立文件）&nbsp;|&nbsp; 评分人：测试团队</div>
</div>

<div class="wrap">

    <!-- ============ 模型代号↔模型名对照表 ============ -->
    <div class="code-map">
        <h2>📌 模型代号对照（任务产物目录 → 报告中模型名）</h2>
        <div class="mapping">
            <div class="m-item">
                <div class="m-code">pjq</div>
                <div class="m-name">GU7C3</div>
                <div class="m-note">121CR0交白卷 · CANoe XL Driver待完成 · Map中规中矩</div>
            </div>
            <div class="m-item">
                <div class="m-code">8qq</div>
                <div class="m-name">1KDF3</div>
                <div class="m-note">Word路径写死Linux · Map解析满分 · CANoe轮询代事件</div>
            </div>
            <div class="m-item">
                <div class="m-code">prz</div>
                <div class="m-name">Y6W5G</div>
                <div class="m-note">CANoe满分 · Word术语替换写成pass · Map intc误分类</div>
            </div>
        </div>
    </div>

    <!-- ============ 评测总览：每模型每任务一句话总结 ============ -->
    <div class="overview">

        <!-- Y6W5G -->
        <div class="ov-card">
            <h3>Y6W5G <span class="avg-badge">均 7.3</span></h3>
            <div class="ov-task">
                <div class="tname">121CR0 Word</div>
                <div class="tscore">
                    <span class="score-pill s-warn">6/10</span>
                    <span class="score-pill s-total">4+1+1</span>
                </div>
                <div class="t-desc">完成了10个文档处理，但 terminology_fixes 逻辑全写成了 pass，dead code明显，日期也写错。</div>
            </div>
            <div class="ov-task">
                <div class="tname">WT2GYB CANoe</div>
                <div class="tscore">
                    <span class="score-pill s-ok">9/10</span>
                    <span class="score-pill s-total">5+3+1</span>
                </div>
                <div class="t-desc">满分，Ethernet四层防护滴水不漏，WithEvents事件监听完整，require_admin()细节到位。</div>
            </div>
            <div class="ov-task">
                <div class="tname">BEOG6I Map</div>
                <div class="tscore">
                    <span class="score-pill s-warn">7/10</span>
                    <span class="score-pill s-total">4+2+1</span>
                </div>
                <div class="t-desc">功能最丰富（地址分布统计、Top30模块），但 .intc_vector 误归为 RAM，中断向量表分类错误。</div>
            </div>
        </div>

        <!-- 1KDF3 -->
        <div class="ov-card">
            <h3>1KDF3 <span class="avg-badge">均 7.3</span></h3>
            <div class="ov-task">
                <div class="tname">121CR0 Word</div>
                <div class="tscore">
                    <span class="score-pill s-ok">7/10</span>
                    <span class="score-pill s-total">4+2+1</span>
                </div>
                <div class="t-desc">10个V3.0文档全部生成，履历表写入完整，结构清晰；但 BASE_DIR 写死 Linux 路径，Windows 直接报错。</div>
            </div>
            <div class="ov-task">
                <div class="tname">WT2GYB CANoe</div>
                <div class="tscore">
                    <span class="score-pill s-warn">6/10</span>
                    <span class="score-pill s-total">3+2+1</span>
                </div>
                <div class="t-desc">CANoe启动带5次重试防busy，通道映射逻辑完整；用轮询替代WithEvents，不符合需求要求，扣2分。</div>
            </div>
            <div class="ov-task">
                <div class="tname">BEOG6I Map</div>
                <div class="tscore">
                    <span class="score-pill s-ok">9/10</span>
                    <span class="score-pill s-total">5+3+1</span>
                </div>
                <div class="t-desc">满分！.data段 ROM+RAM 双重分类，rom_total 和 ram_total 同时叠加 both_sections，设计精妙。</div>
            </div>
        </div>

        <!-- GU7C3 -->
        <div class="ov-card">
            <h3>GU7C3 <span class="avg-badge">均 5.7</span></h3>
            <div class="ov-task">
                <div class="tname">121CR0 Word</div>
                <div class="tscore">
                    <span class="score-pill s-bad">2/10</span>
                    <span class="score-pill s-total">0+0+1</span>
                </div>
                <div class="t-desc">只交付了原始docx，没有任何处理痕迹，无V3.0版本，无脚本，无变更履历，需求完成度0分封顶。</div>
            </div>
            <div class="ov-task">
                <div class="tname">WT2GYB CANoe</div>
                <div class="tscore">
                    <span class="score-pill s-ok">8/10</span>
                    <span class="score-pill s-total">4+3+1</span>
                </div>
                <div class="t-desc">6模块分层结构清晰，WithEvents正确，apply→verify闭环完整；XL Driver 枚举留TODO，用模拟数据。</div>
            </div>
            <div class="ov-task">
                <div class="tname">BEOG6I Map</div>
                <div class="tscore">
                    <span class="score-pill s-warn">7/10</span>
                    <span class="score-pill s-total">4+2+1</span>
                </div>
                <div class="t-desc">未分类sections单独列出方便核查，11类分类细致；.data段未区分ROM+RAM双重身份，精度不如1KDF3。</div>
            </div>
        </div>
    </div><!-- end overview -->

    <!-- ============ 综合排名表 ============ -->
    <table class="score-table">
        <tr>
            <th>排名</th>
            <th>模型</th>
            <th>代号</th>
            <th>121CR0 Word</th>
            <th>WT2GYB CANoe</th>
            <th>BEOG6I Map</th>
            <th>平均分</th>
        </tr>
        <tr>
            <td class="rank">🥇</td>
            <td><strong>Y6W5G</strong></td>
            <td><code style="color:#e07020;font-weight:700;">prz</code></td>
            <td class="t-warn">6/10</td><td class="t-ok">9/10</td><td class="t-warn">7/10</td>
            <td class="t-total">7.3</td>
        </tr>
        <tr>
            <td class="rank">🥈</td>
            <td><strong>1KDF3</strong></td>
            <td><code style="color:#e07020;font-weight:700;">8qq</code></td>
            <td class="t-ok">7/10</td><td class="t-warn">6/10</td><td class="t-ok">9/10</td>
            <td class="t-total">7.3</td>
        </tr>
        <tr>
            <td class="rank">🥉</td>
            <td><strong>GU7C3</strong></td>
            <td><code style="color:#e07020;font-weight:700;">pjq</code></td>
            <td class="t-bad">2/10</td><td class="t-ok">8/10</td><td class="t-warn">7/10</td>
            <td class="t-total">5.7</td>
        </tr>
    </table>

    <!-- ============ 任务小卡片 ============ -->
    <div class="task-pills">
        <div class="task-pill">
            <h4>121CR0 Word文档</h4>
            <div class="t-tag">批量修改10个文档·V3.0升级·变更履历</div>
            <div class="pills">
                <span class="pill ok">1KDF3 7</span>
                <span class="pill warn">Y6W5G 6</span>
                <span class="pill danger">GU7C3 2</span>
            </div>
        </div>
        <div class="task-pill">
            <h4>WT2GYB CANoe测试</h4>
            <div class="t-tag">JSONC解析·硬件识别·通道映射·禁碰Ethernet</div>
            <div class="pills">
                <span class="pill ok">Y6W5G 9</span>
                <span class="pill ok">GU7C3 8</span>
                <span class="pill warn">1KDF3 6</span>
            </div>
        </div>
        <div class="task-pill">
            <h4>BEOG6I Map解析</h4>
            <div class="t-tag">Green Hills map·ROM/RAM分类·内存汇总</div>
            <div class="pills">
                <span class="pill ok">1KDF3 9</span>
                <span class="pill warn">Y6W5G 7</span>
                <span class="pill warn">GU7C3 7</span>
            </div>
        </div>
    </div>

</div><!-- end wrap -->

<div class="ft">
    评测报告 &nbsp;|&nbsp; 生成时间：2026-05-12 &nbsp;|&nbsp; 佐证截图 9 张（独立文件）&nbsp;|&nbsp; 评分人：测试团队
</div>

</body>
</html>'''

out_path = os.path.join(OUT, 'eval_report_20260512.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(HTML)
sz = os.path.getsize(out_path)
print(f'[OK] Report: {out_path}')
print(f'     Size: {sz//1024} KB')
print(f'     Screenshots: 9 (独立文件，未嵌入HTML)')
