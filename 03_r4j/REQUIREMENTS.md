# V 模型需求-测试追溯统计工具（当前实现版需求）

## 1. 文档目的

这份文档用于把 `apple/03_r4j` 的现有实现能力完整交接给另一个 AI，目标是做出“功能基本一致”的工具。  
本版本优先描述“当前代码真实行为”，不是初版设想。

## 2. 工具目标与范围

| 项目 | 说明 |
|---|---|
| 工具目标 | 从 Jira(R4J) 拉取需求、从 Confluence 附件读取测试用例，产出覆盖率/通过率统计报表 |
| 入口脚本 | `v_model_tracer.py` |
| 报告类型 | `coverage`、`pass-rate`（二选一） |
| 当前定位 | 数据拉取 + 统计分析 + Excel 报告导出 |

## 3. 技术栈与依赖

| 类别 | 内容 |
|---|---|
| 语言 | Python 3 |
| 核心依赖 | `requests`, `python-dotenv`, `openpyxl`, `PyYAML` |
| 依赖文件 | `requirements.txt` |

## 4. 核心流程（必须复刻）

| 步骤 | 行为 |
|---|---|
| 1. 读取配置 | 从 `--config` 指定 YAML 读取配置，写入 `_project_root` 与 `_config_name` |
| 2. 加载需求 | 按 `r4j_projects` 逐项拉取 R4J 树，保留有 `key` 的 Issue 项 |
| 3. 拉取字段 | 对每个 Issue 再调用 Jira Issue API 补齐 `components/issuetype/labels/priority` |
| 4. 加载用例 | 按 `confluence_testcases` 拉取页面（可选遍历子页）并下载 Excel 附件 |
| 5. 解析用例 | 解析匹配 Sheet，识别 ID/名称/追溯列/结果列，提取需求 key 集合 |
| 6. 统计分析 | 根据 `report-type` 计算覆盖率或通过率相关统计 |
| 7. 导出报告 | 输出到 `tempFile/reports/YYYYMMDD/*.xlsx` |

## 5. 输入与配置要求

### 5.1 环境变量

| 变量名 | 用途 | 必需 |
|---|---|---|
| `JIRA_TOKEN` | Jira 鉴权 | 是 |
| `JIRA_URL` | Jira 基础地址（默认 `https://jira.i-soft.com.cn`） | 否 |
| `CONFLUENCE_URL` | Confluence 基础地址 | 是 |
| `CONFLUENCE_USERNAME` | Confluence 用户名 | 是 |
| `CONFLUENCE_API_TOKEN` | Confluence Token | 是 |
| `CONFLUENCE_AUTH_MODE` | `bearer` 或 `basic`，默认 `bearer` | 否 |

说明：代码通过 `02_skills/token-manager/.env` 加载以上变量。

### 5.2 配置文件关键结构

| 配置块 | 关键字段 | 说明 |
|---|---|---|
| `r4j_projects` | `name/node_id/project_id/level` | 定义需求来源与层级 |
| `confluence_testcases` | `page_id/test_type/traverse_children` | 定义测试用例来源 |
| `confluence_testcases.excel_columns` | `id/name/trace/result` | Excel 列映射 |
| `confluence_testcases.sheet_pattern` | 正则字符串 | 筛选 Sheet |
| `confluence_testcases.result_mapping` | `passed/failed/not_executed` | 结果映射 |
| `cache` | `enabled/ttl_hours/dir/namespace` | 缓存策略 |
| `api` | `delay_ms/timeout/retry_times` | 请求节流与重试 |
| `logging` | `level/format` | 日志配置 |

## 6. 命令行接口（当前实现）

| 参数 | 必填 | 说明 |
|---|---|---|
| `--config`, `-c` | 否 | 配置文件路径，默认 `config.yaml` |
| `--no-cache` | 否 | 禁用缓存 |
| `--project`, `-p` | 否 | 按项目名子串过滤 `r4j_projects` |
| `--report-type`, `-r` | 是 | `coverage` 或 `pass-rate` |
| `--verbose`, `-v` | 否 | 强制日志级别为 DEBUG |
| `--output`, `-o` | 否 | 输出文件名（仅文件名） |
| `--log` | 否 | 日志文件名（写入 `tempFile/logs`） |

示例：

```bash
python v_model_tracer.py --config config.yaml --report-type coverage
python v_model_tracer.py --config config_software_test.yaml --report-type pass-rate --no-cache
```

## 7. 数据规则（必须一致）

| 规则项 | 当前实现 |
|---|---|
| 追溯 key 提取 | 正则 `[A-Z]+-\\d+`，支持逗号/空格/换行等混合文本 |
| key 归一化 | 转大写，`_` 转 `-`，兼容破折号噪音字符 |
| 结果值映射 | 先按 `result_mapping` 精确匹配，再 fallback 到 `pass/passed/ok` 与 `fail/failed/ng` |
| 未执行判定 | 空值或未命中映射时视为 `not_executed` |
| 通过率分母 | `passed + failed`（不含 `not_executed`） |

## 8. 报表输出规范（当前实现）

### 8.1 `coverage` 报告

| Sheet 名称 | 内容 |
|---|---|
| `模块概览` | 每个模块未覆盖需求数量与 key 列表（基于 requirement 的 `components`） |
| `覆盖率汇总` | 按 `project + level` 汇总覆盖率 |
| `覆盖率明细` | 每条需求的模块/类型/标签/优先级/是否覆盖 |
| `孤立追溯` | 用例追溯到不存在需求 key 的统计 |

### 8.2 `pass-rate` 报告

| Sheet 名称 | 内容 |
|---|---|
| `通过率统计` | 按模块统计 total/passed/failed/not_executed/pass_rate，含 `TOTAL` 汇总行 |

## 9. 缓存与目录行为

| 项目 | 当前实现 |
|---|---|
| 需求缓存 | `tempFile/cache/<namespace>/requirements/*.json` |
| Jira 字段缓存 | `tempFile/cache/<namespace>/issue_fields_cache.json` |
| 用例附件缓存 | `tempFile/cache/<namespace>/testcases/*`（文件名包含 `page_id + attachment_id + version`） |
| 报告目录 | 固定 `tempFile/reports/YYYYMMDD/` |
| 日志目录 | `tempFile/logs/` |

## 10. 已实现与未实现边界（给复刻 AI 的重点）

### 10.1 已实现

| 能力 | 状态 |
|---|---|
| R4J 树拉取 + Issue 过滤 | 已实现 |
| Confluence 页面/子页面附件拉取 | 已实现 |
| Excel 多 Sheet 解析与表头识别 | 已实现 |
| 覆盖率统计 | 已实现 |
| 通过率统计 | 已实现 |
| Excel 报表格式化输出 | 已实现 |
| 缓存、重试、延迟控制 | 已实现 |

### 10.2 当前代码里“有类/方法但未接入主流程”

| 项目 | 说明 |
|---|---|
| `Tracer.run_full_check` | 主流程未调用，未输出“问题清单/层级一致性检查” |
| `create_trace_matrix_sheet` / `create_issues_sheet` | `generate_report()` 当前不会创建这两类 sheet |

### 10.3 与配置名义不完全一致的点（需保持或显式改进）

| 项目 | 当前行为 |
|---|---|
| `output.dir` | 目前未生效，代码写死到 `tempFile/reports` |
| `output.filename_template` | 目前未生效，文件名由 `report-type + level + timestamp` 生成 |

## 11. 复刻验收标准（最低）

| 验收项 | 判定标准 |
|---|---|
| CLI 对齐 | 支持第 6 节全部参数，`--report-type` 必填 |
| 数据链路对齐 | Jira + Confluence + Excel 解析能跑通 |
| 指标对齐 | 覆盖率与通过率计算口径一致 |
| 报表结构对齐 | sheet 名称与字段结构与第 8 节一致 |
| 缓存行为对齐 | 目录层级与 TTL 行为一致 |
| 容错对齐 | API 重试、超时、日志行为可复现 |

## 12. 建议给另一个 AI 的实现指令（可直接复制）

```text
请基于 Python 实现一个与以下规格“功能基本一致”的工具：
1) 从 Jira R4J 拉需求树（只保留有 key 的 Issue），并补充 issue 字段 components/issuetype/labels/priority；
2) 从 Confluence 指定页面（可递归子页面）下载 Excel 附件，按配置解析测试用例；
3) 支持 report-type=coverage 或 pass-rate；
4) 生成 Excel 报告：
   - coverage: 模块概览/覆盖率汇总/覆盖率明细/孤立追溯
   - pass-rate: 通过率统计（含 TOTAL）
5) 支持缓存、TTL、API 重试、超时、请求延迟、日志输出；
6) CLI 参数与本说明保持一致；
7) 保持追溯 key 提取与结果映射规则一致。
```

---

最后更新时间：2026-05-15
