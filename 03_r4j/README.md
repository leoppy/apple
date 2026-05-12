# V 模型用例-需求双向追溯检查工具

## 项目简介

该工具用于检查测试用例与需求/设计项之间的双向追溯关系，并输出覆盖率与通过率统计报告。

## 当前实现状态（MVP）

| 模块 | 文件 | 状态 |
|---|---|---|
| 主入口 | `v_model_tracer.py` | 已完成 |
| Confluence 客户端 | `modules/confluence_client.py` | 已完成 |
| 需求加载 | `modules/requirement_loader.py` | 已完成 |
| 用例加载 | `modules/testcase_loader.py` | 已完成 |
| 追溯检查 | `modules/tracer.py` | 已完成 |
| 统计分析 | `modules/coverage_analyzer.py` | 已完成 |
| 报告生成 | `modules/report_generator.py` | 已完成 |
| 数据模型 | `modules/models.py` | 已完成 |

## 安装依赖

```bash
python -m pip install -r requirements.txt
```

## 运行方式

```bash
# 推荐：先跑测试配置
python v_model_tracer.py --config config_test.yaml --verbose

# 正式配置
python v_model_tracer.py --config config.yaml
```

## 常用参数

| 参数 | 说明 |
|---|---|
| `--config`, `-c` | 指定配置文件，默认 `config.yaml` |
| `--no-cache` | 禁用缓存并强制刷新数据 |
| `--project`, `-p` | 按项目名过滤（模糊匹配） |
| `--coverage-only` | 仅生成覆盖率/通过率统计（跳过问题检查） |
| `--output`, `-o` | 自定义输出文件名（不含目录） |
| `--verbose`, `-v` | 打开调试日志 |
| `--log` | 写入日志文件 |

## 报告输出

输出目录：`tempFile/reports`

Excel 报告包含 4 个 Sheet：

1. `追溯矩阵`
2. `覆盖率统计`
3. `问题清单`
4. `通过率统计`

## 说明

1. 需求数据来自 Jira Requirements（R4J API）。
2. 测试用例来自 Confluence 页面附件（Excel）。
3. 缓存默认开启，目录由配置项 `cache.dir` 决定。
4. Confluence 认证默认使用 Bearer Token（环境变量 `CONFLUENCE_AUTH_MODE=bearer`）。
