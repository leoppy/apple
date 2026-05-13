---
name: interview-question-kit
description: 用于面试官快速出题与题库管理。凡是用户提到“出面试题/面试题库/根据简历出题/筛选面试题”，都应触发本 skill。先给候选题梗概供面试官选择，再生成最终面试题文档。
---

# 面试出题 Skill

## 核心约束

| 规则 | 要求 |
|---|---|
| 两阶段流程 | 必须先输出候选题梗概清单，待面试官选择后再生成最终题单 |
| 题库范围 | 题库只允许通用题：`question_bank/common/` |
| 定制题入库 | 禁止把任何定制题写入题库；定制题只出现在当次输出文档 |
| 定制标识 | 候选题清单中每道题必须标注 `通用` 或 `定制` |
| 默认配比 | 用户无特殊要求时，按 `定制:通用 = 2:1` 组织候选题 |

## 目录约定
- `question_bank/common/`：通用题库（每题一个 `.md`）
- `outputs/`：每次输出（候选清单、最终题单）
- `scripts/`：辅助脚本
- `references/`：标签与模板说明

## 单题文件格式（仅题库）
题库中的每道通用题必须遵循：

```md
---
id: G001
tags: [通用基础, 工程习惯]
type: 通用题
difficulty: 校招
---

# 题目
...

# 参考答案
...

# 追问
...
```

## 执行流程（必须按顺序）

| 阶段 | 动作 | 输出 |
|---|---|---|
| A 候选阶段 | 读取需求（岗位/题量/标签/简历），生成候选题梗概清单，并标注 `通用/定制` | `outputs/<姓名>_候选题梗概.md` |
| B 选择阶段 | 面试官选择题号，必要时替换或增删 | 聊天中确认“最终入选题号” |
| C 定稿阶段 | 基于已选题生成最终面试题文档 | `outputs/<姓名>_面试题.md` |

## 候选题配比
- 默认：`定制:通用 = 2:1`
- 如果总题量不能整除，优先保证“定制题数量不低于通用题数量”。
- 若用户明确指定配比，以用户要求为准。

## 定制题规则
- 定制题可以根据简历生成。
- 定制题必须在候选梗概和最终题单中标注为 `定制（不入库）`。
- 定制题严禁写入 `question_bank/common/`。

## 推荐脚本
1. 生成候选题梗概（含 `通用/定制` 标注）
- `python scripts/generate_question_outline.py --candidate "<姓名>" --total 6 --tags "项目深挖,场景题" --resume-txt "outputs/<姓名>_resume.txt"`

2. 按选题号生成最终题单
- `python scripts/finalize_interview_doc.py --candidate "<姓名>" --outline-json "outputs/<姓名>_候选题梗概.json" --pick "1,2,4"`

3. 题库合规检查（确保无定制题入库）
- `python scripts/validate_question_bank.py --bank-dir "question_bank/common"`
