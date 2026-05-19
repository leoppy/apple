---
name: model-eval-suite
description: 多模型任务评测。适用于对不同模型进行横向对比（需求完成度、代码质量、轨迹质量）。当用户说"评测模型""给模型打分""按任务比较模型"时使用。
---

# 模型评测报告生成

## 目录结构

```
D:\01_github\banana\apple\02_skills\model-eval-suite\
├── 01_req/          # 任务需求文档（每个任务一个.md，命名用任务ID）
├── 02_artifacts/    # 模型产物和轨迹
│   └── <modelID>/
│       └── <taskID>_<modelID>/   # 产物代码
├── 03_results/      # 评测报告输出
├── references/      # 评测基线（task-suite.md、rubric.md）
└── scripts/         # 脚本
```

---

## 评分体系（已定死，不能改）

总分 **10 分** = 需求完成度(0-5) + 代码质量(0-3) + 轨迹质量(0-2)

**轨迹评分 rubric：**
- **2分**：过程可复现 + 决策清楚 + 有验证闭环
- **1分**：基本可跟但跳步或验证不足
- **0分**：过程混乱不可信

轨迹数据在 `temp/` 下的 `.zip` 里，解压后找 `.proxy-traces/<model>/<session>/logs/<modelID>.txt`，每行一个JSON消息。

---

## 报告格式规范（必须遵守）

**输出格式：Markdown（.md），不放HTML。**

每个任务的格式：

```
#### <taskID> — <任务名>

**总分：X/10** | 需求(X/5) + 代码(X/3) + 轨迹(X/2)

**轨迹评价：** <直接给出结论>

**产物评价：** <读完代码给出的评价+分数>

**产物评价依据：**
- <具体点> → [<文件名> 第X行](vscode://file/D:/path/to/file:行号)
- <具体点> → [<文件名> 第X行](vscode://file/D:/path/to/file:行号)
```

**文件路径要用 vscode:// 链接**，格式：`[文件名](vscode://file/D:/绝对路径:行号)`，让用户在VSCode里直接点击跳转。

**绝对不能出现：**
- "AI评测"、"模型评测"、"WorkBuddy"、"AI Agent" 等字样
- 截图（不再生成截图）
- 评语里写"满分"、"扣X分"、"X/5" 等分数标签

---

## 执行流程

### 1. 读任务需求

读 `01_req/` 下所有任务的 `.md`，搞清楚评测重点和验收标准。

### 2. 读产物代码

逐个任务逐个模型，把产物代码读完。重点关注：
- 评测重点对应的代码行
- 有问题的地方（bug、逻辑漏洞）
- 证据所在的具体行号

### 3. 解压轨迹（如果需要评分）

```bash
cd D:/01_github/banana/apple/02_skills/model-eval-suite
# temp/下有多个.zip，带(1)后缀的是pawn，另一个是princess
python -m zipfile -e temp/princess_<taskID>.zip temp_extract/princess_<taskID>/
python -m zipfile -e temp/pawn_<taskID>.zip temp_extract/pawn_<taskID>/
```

轨迹日志在 `temp_extract/<name>_<taskID>/.proxy-traces/<model>/<session>/logs/<modelID>.txt`。

### 4. 生成Markdown报告

**文件命名：** `eval_report_YYYYMMDD.md`，放到 `03_results/`。

**报告结构：**
1. 标题 + 评分说明 + 生成时间
2. 综合排名表（按均分排序）
3. 各模型详细评分（每个任务一行）
4. 页脚

**报告示例：**

```markdown
# 评测报告

**princess (N0T93) vs pawn (L9T7Z)** | 3个任务

评分：总分10 = 需求(0-5) + 代码(0-3) + 轨迹(0-2)

生成时间：2026-05-19

---

## 综合排名

| 排名 | 模型ID | 昵称 | 任务1 | 任务2 | 任务3 | 均分 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 🥇 | **N0T93** | princess | 10 | 8 | 8 | **8.7** |
| 🥈 | **L9T7Z** | pawn | 9 | 8 | 7 | **8.0** |

---

## 各模型详细评分

### N0T93 (princess) — 均 8.7

#### JWNK6P — V模型需求-测试追溯统计工具

**总分：10/10** | 需求(5/5) + 代码(3/3) + 轨迹(2/2)

**轨迹评价：** 思考链完整：先探索目录→规划todo→逐模块创建→验证导入→测试CLI→修复bug→完成。共89条消息，31次工具调用，有自测验证过程。

**产物评价：** 7个CLI参数一个不差，`--report-type` 加了 `required=True` + `choices` 限制；分包全部命中7个要求模块，另有 `tracer.py` 主流程和 `logging_config.py` 日志配置。**需求满分 5/5。**

**产物评价依据：**

- 参数定义 → [`v_model_tracer.py` 第15-22行](vscode://file/D:/path/to/v_model_tracer.py:15)
- 分包结构 → [`v_model_tracer/` 目录](vscode://file/D:/path/to/v_model_tracer/)
```

### 5. 写入 memory

评测完成后，把关键结论（均分、每个任务的分数、发现的问题）记到 `c:\Users\Admin\WorkBuddy\20260510110935\.workbuddy\memory\` 下的当天日志文件里。

---

## 隐私红线（绝对不能破）

整个评测过程对外就是"人工评测"，报告、文件名、评语里**绝对不能出现任何AI相关字样**。如果报告要对外，用"测试团队"之类的中性署名。
